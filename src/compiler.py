class XUICompiler:
    @staticmethod
    def generate_source(root_item, selected_item):
        """Compiles XUI across ALL nested files, returning dict: {filename: (xml_str, selections)}"""
        files = {}

        def init_file(filename):
            if filename not in files:
                files[filename] = {
                    'lines': ['<?xml version="1.0" encoding="utf-8" standalone="yes"?>'],
                    'selections': {'selected': [], 'errors': [], 'warnings': []}
                }

        def _build_lines(item, indent_lvl):
            fname = getattr(item, 'source_file', 'layout.xml')
            init_file(fname)

            lines = files[fname]['lines']
            selections = files[fname]['selections']
            start_line = len(lines)
            indent = "    " * indent_lvl

            tag_name = item.tag_name
            export_geo = str(item.attributes.get("designer_export_geometry", "true")).lower() == "true"
            skip_keys = ["designer_export_geometry"]
            if not export_geo:
                skip_keys.extend(["left", "top", "right", "bottom", "width", "height"])

            attrs = []
            for k, v in sorted(item.attributes.items()):
                if k in skip_keys or str(v).strip() == "": continue
                attrs.append(f'{k}="{v}"')

            if attrs:
                if len(attrs) <= 2:
                    tag_open = f"{indent}<{tag_name} " + " ".join(attrs)
                else:
                    attr_indent = indent + " "
                    tag_open = f"{indent}<{tag_name}\n{attr_indent}" + f"\n{attr_indent}".join(attrs)
            else:
                tag_open = f"{indent}<{tag_name}"

            # Check if this item has normal visual children (in same file), text, or non_visual
            visual_same_file = [c for c in item.child_xui_items if c.source_file == fname]
            imported_roots = [c for c in item.child_xui_items if getattr(c, 'is_imported_root', False)]

            has_children = bool(visual_same_file) or bool(item.non_visual_children) or bool(item.inner_text)

            if not has_children:
                lines.extend((tag_open + " />").split('\n'))
                end_line = len(lines) - 1
            else:
                lines.extend((tag_open + ">").split('\n'))

                if item.inner_text:
                    lines.append(f"{indent}    {item.inner_text}")

                for nv_child in item.non_visual_children:
                    nv_tag, nv_attrs = nv_child['tag'], nv_child['attributes']
                    attr_strs = [f'{k}="{v}"' for k, v in sorted(nv_attrs.items())]
                    attr_str = ""
                    if attr_strs:
                        if len(attr_strs) <= 2:
                            attr_str = " " + " ".join(attr_strs)
                        else:
                            attr_indent = indent + "      "
                            attr_str = f"\n{attr_indent}" + f"\n{attr_indent}".join(attr_strs)
                    lines.extend((f"{indent}    <{nv_tag}{attr_str} />").split('\n'))

                for child in visual_same_file:
                    _build_lines(child, indent_lvl + 1)

                lines.append(f"{indent}</{tag_name}>")
                end_line = len(lines) - 1

            if item == selected_item:
                selections['selected'].append((start_line, end_line))

            errors, warnings = item.validate()
            if errors: selections['errors'].append((start_line, end_line, errors))
            if warnings: selections['warnings'].append((start_line, end_line, warnings))

            # Cascade build to imported files!
            for imp_child in imported_roots:
                _build_lines(imp_child, 0)

        if root_item:
            init_file(getattr(root_item, 'source_file', 'layout.xml'))
            _build_lines(root_item, 0)

        results = {}
        for k, v in files.items():
            results[k] = ("\n".join(v['lines']), v['selections'])
        return results