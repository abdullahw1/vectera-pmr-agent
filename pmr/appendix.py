"""Place source exhibits on Letter paper without rasterizing or changing values."""
import re
import statistics

import fitz


def append_exhibits(result, source, approved=False):
    with fitz.open(source) as document:
        for index, original in enumerate(document):
            spans = [s for b in original.get_text("dict")["blocks"] if "lines" in b
                     for line in b["lines"] for s in line["spans"] if s["text"].strip()]
            if not spans:
                raise ValueError("Appendix exhibit has no readable text; manual layout review required")
            bounds = fitz.Rect(spans[0]["bbox"])
            for span in spans[1:]:
                bounds |= fitz.Rect(span["bbox"])
            bounds = (bounds + (-14, -20, 14, 14)) & original.rect
            font = statistics.median(s["size"] for s in spans)
            # Keep the entire original exhibit where it is readable. Wide tables
            # are split at column groups, with the investment-name column repeated.
            width, height = 612, 792
            available_width, available_height = width - 72, height - 110
            scale = min(available_width / bounds.width, available_height / bounds.height)
            panels = [(bounds, None)]
            if font * scale < 7:
                tables = original.find_tables().tables
                if len(tables) != 1:
                    raise ValueError("Wide appendix needs an unambiguous table for readable panel layout")
                table = tables[0]
                cells = next(row.cells for row in table.rows if row.cells[0])
                label_end = cells[0][2]
                cuts = sorted({cell[0] for row in table.rows for cell in row.cells if cell})
                # Annual-return group headings should not be separated from their subcolumns.
                for row, values in zip(table.rows[:5], table.extract()[:5]):
                    groups = [cell[0] for cell, value in zip(row.cells, values)
                              if cell and value and re.search(r"\b(?:year|quarter|inception)\b", value, re.I)]
                    if len(groups) >= 2:
                        cuts = groups
                        break
                minimum_scale = 7 / font
                if bounds.height * minimum_scale > available_height:
                    raise ValueError("Appendix height cannot fit at readable type size")
                capacity = available_width / minimum_scale
                panels = []
                start = bounds.x0
                while start < bounds.x1 - .5:
                    repeat = None if not panels else fitz.Rect(bounds.x0, bounds.y0, label_end, bounds.y1)
                    repeated_width = repeat.width if repeat else 0
                    limit = start + capacity - repeated_width
                    end = bounds.x1 if bounds.x1 <= limit else max(
                        (x for x in cuts if start + 1 < x <= limit), default=None)
                    if end is None:
                        raise ValueError("Appendix column group cannot fit at readable type size")
                    panels.append((fitz.Rect(start, bounds.y0, end, bounds.y1), repeat))
                    start = end
            largest_width = max(clip.width + (repeat.width if repeat else 0) for clip, repeat in panels)
            scale = min(available_width / largest_width, available_height / bounds.height, 1)
            compact_scale = 7 / font
            if len(panels) > 1 and len(panels) * bounds.height * compact_scale + 40 * (len(panels) - 1) <= available_height:
                scale = min(scale, compact_scale)
            page, bottom = None, height
            for panel_index, (clip, repeat) in enumerate(panels):
                if bottom + 45 + clip.height * scale > height - 45:
                    page = result.new_page(width=width, height=height)
                    heading_y, y = 32, 65
                    page.insert_text((36, height - 25), f"Page {len(result)}" + (" | DRAFT" if not approved else ""), fontsize=8)
                else:
                    heading_y, y = bottom + 23, bottom + 40
                x = 36
                if repeat:
                    rect = fitz.Rect(x, y, x + repeat.width * scale, y + repeat.height * scale)
                    page.show_pdf_page(rect, document, index, clip=repeat)
                    x = rect.x1
                rect = fitz.Rect(x, y, x + clip.width * scale, y + clip.height * scale)
                page.show_pdf_page(rect, document, index, clip=clip)
                label = f"Appendix A | Flash source page {index + 1}"
                if len(panels) > 1:
                    label += f" | Panel {panel_index + 1} of {len(panels)} (investment names repeated)"
                page.insert_text((36, heading_y), label, fontsize=9, color=(.106, .165, .29))
                bottom = rect.y1
