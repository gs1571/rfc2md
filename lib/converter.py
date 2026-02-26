"""
XML to Markdown converter module.

This module contains the XmlToMdConverter class for converting RFC XML v3 documents
to well-formatted Markdown.
"""

import logging
from pathlib import Path

from lxml import etree


class XmlToMdConverter:
    """
    Converter class for transforming RFC XML v3 documents to Markdown format.

    This class handles parsing of RFC XML files and conversion to well-formatted
    Markdown, including metadata, sections, and various RFC-specific elements.
    """

    def __init__(self, xml_file):
        """
        Initialize the converter with an XML file.

        Args:
            xml_file: Path to the RFC XML file
        """
        self.xml_file = Path(xml_file)
        self.logger = logging.getLogger(__name__)
        self.tree = None
        self.root = None
        self.markdown_lines = []
        self.section_depth = 0
        self.toc_entries = []  # For TOC generation
        self.section_id_to_anchor = {}  # Mapping from section pn to anchor

    def _build_section_anchor_mapping(self):
        """
        Build mapping from section pn to anchor by pre-scanning all sections.
        This must be called before TOC generation.
        """
        # Process middle sections
        middle = self.root.find("middle")
        if middle is not None:
            for section in middle.findall("section"):
                self._collect_section_anchors(section)

        # Process back sections
        back = self.root.find("back")
        if back is not None:
            for section in back.findall("section"):
                self._collect_section_anchors(section)

    def _collect_section_anchors(self, section):
        """
        Recursively collect pn to anchor mappings from section tree.

        Args:
            section: XML section element
        """
        pn = section.get("pn", "")
        anchor = section.get("anchor", "")

        if pn and anchor:
            self.section_id_to_anchor[pn] = anchor

        # Process nested sections recursively
        for subsection in section.findall("section"):
            self._collect_section_anchors(subsection)

    def convert(self):
        """
        Convert the RFC XML to Markdown format.

        Returns:
            String containing the complete Markdown document
        """
        self.logger.info(f"Parsing XML file: {self.xml_file}")

        # Parse XML with namespace handling
        try:
            self.tree = etree.parse(str(self.xml_file))
            self.root = self.tree.getroot()
        except etree.XMLSyntaxError as e:
            raise ValueError(f"Invalid XML syntax: {e}") from e
        except Exception as e:
            raise ValueError(f"Error parsing XML: {e}") from e

        # Extract namespace
        self.ns = {"rfc": "http://www.w3.org/2001/XInclude"} if self.root.nsmap else {}

        # Process document sections
        self._process_front()

        # Build section anchor mapping BEFORE generating TOC
        self._build_section_anchor_mapping()

        # Generate and insert TOC after front matter
        toc_lines = self._generate_toc()
        if toc_lines:
            self.markdown_lines.extend(toc_lines)

        self._process_middle()
        self._process_back()

        return "\n".join(self.markdown_lines)

    def _process_front(self):
        """Process the <front> section containing metadata and abstract."""
        front = self.root.find("front")
        if front is None:
            return

        # Extract title
        title_elem = front.find("title")
        if title_elem is not None:
            title = title_elem.text or ""
            abbrev = title_elem.get("abbrev", "")
            self.markdown_lines.append(f"# {title}")
            if abbrev and abbrev != title:
                self.markdown_lines.append(f"*({abbrev})*")
            self.markdown_lines.append("")

        # Extract seriesInfo
        series_info = front.find("seriesInfo")
        if series_info is not None:
            rfc_name = series_info.get("name", "")
            rfc_value = series_info.get("value", "")
            stream = series_info.get("stream", "")
            if rfc_name and rfc_value:
                self.markdown_lines.append(f"**{rfc_name} {rfc_value}**")
                if stream:
                    self.markdown_lines.append(f"*Stream: {stream}*")
                self.markdown_lines.append("")

        # Extract document metadata from root element
        metadata_fields = []

        category = self.root.get("category", "")
        if category:
            metadata_fields.append(f"**Category:** {category}")

        obsoletes = self.root.get("obsoletes", "")
        if obsoletes:
            metadata_fields.append(f"**Obsoletes:** {obsoletes}")

        updates = self.root.get("updates", "")
        if updates:
            metadata_fields.append(f"**Updates:** {updates}")

        submission_type = self.root.get("submissionType", "")
        if submission_type:
            metadata_fields.append(f"**Submission Type:** {submission_type}")

        consensus = self.root.get("consensus", "")
        if consensus:
            metadata_fields.append(f"**Consensus:** {consensus}")

        ipr = self.root.get("ipr", "")
        if ipr:
            metadata_fields.append(f"**IPR:** {ipr}")

        doc_name = self.root.get("docName", "")
        if doc_name:
            metadata_fields.append(f"**Doc Name:** {doc_name}")

        # Add metadata fields if any exist
        if metadata_fields:
            for field in metadata_fields:
                self.markdown_lines.append(field)
            self.markdown_lines.append("")

        # Extract authors
        authors = front.findall("author")
        if authors:
            self.markdown_lines.append("## Authors")
            self.markdown_lines.append("")
            for author in authors:
                fullname = author.get("fullname", "")
                initials = author.get("initials", "")
                surname = author.get("surname", "")
                role = author.get("role", "")

                author_line = fullname or f"{initials} {surname}".strip()
                if role == "editor":
                    author_line += " *(Editor)*"
                self.markdown_lines.append(f"- {author_line}")

                # Organization
                org = author.find("organization")
                if org is not None and org.text:
                    self.markdown_lines.append(f"  - {org.text}")

                # Email
                address = author.find("address")
                if address is not None:
                    email = address.find("email")
                    if email is not None and email.text:
                        self.markdown_lines.append(f"  - Email: {email.text}")

            self.markdown_lines.append("")

        # Extract date
        date_elem = front.find("date")
        if date_elem is not None:
            month = date_elem.get("month", "")
            year = date_elem.get("year", "")
            day = date_elem.get("day", "")

            date_str = ""
            if day:
                date_str = f"{day} "
            if month:
                date_str += f"{month} "
            if year:
                date_str += year

            if date_str:
                self.markdown_lines.append(f"**Date:** {date_str.strip()}")
                self.markdown_lines.append("")

        # Extract area and workgroup
        area = front.find("area")
        if area is not None and area.text:
            self.markdown_lines.append(f"**Area:** {area.text}")
            self.markdown_lines.append("")

        workgroup = front.find("workgroup")
        if workgroup is not None and workgroup.text:
            self.markdown_lines.append(f"**Workgroup:** {workgroup.text}")
            self.markdown_lines.append("")

        # Extract keywords
        keywords = front.findall("keyword")
        if keywords:
            keyword_list = [kw.text for kw in keywords if kw.text]
            if keyword_list:
                self.markdown_lines.append(f"**Keywords:** {', '.join(keyword_list)}")
                self.markdown_lines.append("")

        # Extract links
        links = self.root.findall("link")
        if links:
            self.markdown_lines.append("## Related Documents")
            self.markdown_lines.append("")
            for link in links:
                href = link.get("href", "")
                rel = link.get("rel", "")
                if href:
                    self.markdown_lines.append(f"- [{rel or 'Link'}]({href})")
            self.markdown_lines.append("")

        # Extract abstract
        abstract = front.find("abstract")
        if abstract is not None:
            self.markdown_lines.append("## Abstract")
            self.markdown_lines.append("")
            for t_elem in abstract.findall("t"):
                text = self._get_element_text(t_elem)
                if text:
                    indent = t_elem.get("indent", "0")
                    if indent != "0":
                        text = "  " * int(indent) + text
                    self.markdown_lines.append(text)
                    self.markdown_lines.append("")

        # Extract boilerplate sections
        boilerplate = front.find("boilerplate")
        if boilerplate is not None:
            for section in boilerplate.findall("section"):
                self._process_boilerplate_section(section)

    def _generate_toc(self):
        """
        Generate Table of Contents from the XML <toc> section or from collected entries.

        Returns:
            List of markdown lines for TOC
        """
        toc_lines = []
        toc_lines.append("## Table of Contents")
        toc_lines.append("")

        # Try to extract TOC from XML first
        front = self.root.find("front")
        if front is not None:
            toc_elem = front.find("toc")
            if toc_elem is not None:
                toc_section = toc_elem.find("section")
                if toc_section is not None:
                    # Process TOC entries from XML
                    ul = toc_section.find("ul")
                    if ul is not None:
                        self._process_toc_list(ul, toc_lines, depth=0)
                        toc_lines.append("")
                        return toc_lines

        # Fallback: use collected entries (if any)
        if self.toc_entries:
            for entry in self.toc_entries:
                depth = entry["depth"]
                title = entry["title"]
                anchor = entry["anchor"]
                number = entry.get("number", "")

                indent = "  " * (depth - 1)

                if number:
                    toc_lines.append(f"{indent}- [{number}. {title}](#{anchor})")
                else:
                    toc_lines.append(f"{indent}- [{title}](#{anchor})")

            toc_lines.append("")

        return toc_lines

    def _process_toc_list(self, ul_elem, toc_lines, depth=0):
        """
        Process TOC list recursively from XML.

        Args:
            ul_elem: XML ul element from TOC
            toc_lines: List to append TOC lines to
            depth: Current nesting depth
        """
        indent = "  " * depth

        for li in ul_elem.findall("li"):
            # Get the text content and xref
            t_elem = li.find("t")
            if t_elem is not None:
                xrefs = t_elem.findall("xref")
                if len(xrefs) >= 2:
                    # First xref is section number, second is title
                    num_xref = xrefs[0]
                    title_xref = xrefs[1]

                    target = num_xref.get("target", "")
                    section_num = num_xref.get("derivedContent", "")
                    # Try derivedContent first, then text content
                    title = title_xref.get("derivedContent", "") or title_xref.text or ""

                    if section_num and title:
                        toc_lines.append(
                            f"{indent}- [{section_num}. {title}](#{self.section_id_to_anchor.get(target, target)})"
                        )
                    elif title:
                        toc_lines.append(
                            f"{indent}- [{title}](#{self.section_id_to_anchor.get(target, target)})"
                        )
                elif len(xrefs) == 1:
                    # Only one xref - could be unnumbered section
                    xref = xrefs[0]
                    target = xref.get("target", "")
                    # Try derivedContent first, then text content
                    title = xref.get("derivedContent", "") or xref.text or ""
                    if title:
                        toc_lines.append(
                            f"{indent}- [{title}](#{self.section_id_to_anchor.get(target, target)})"
                        )

            # Process nested lists
            nested_ul = li.find("ul")
            if nested_ul is not None:
                self._process_toc_list(nested_ul, toc_lines, depth + 1)

    def _process_boilerplate_section(self, section):
        """Process boilerplate sections like Status of This Memo."""
        name_elem = section.find("name")
        if name_elem is not None and name_elem.text:
            self.markdown_lines.append(f"## {name_elem.text}")
            self.markdown_lines.append("")

        for t_elem in section.findall("t"):
            text = self._get_element_text(t_elem)
            if text:
                self.markdown_lines.append(text)
                self.markdown_lines.append("")

    def _process_middle(self):
        """Process the <middle> section containing main content."""
        middle = self.root.find("middle")
        if middle is None:
            return

        # Process all sections
        for section in middle.findall("section"):
            self._process_section(section, depth=1)

    def _process_back(self):
        """Process the <back> section containing references and appendices."""
        back = self.root.find("back")
        if back is None:
            return

        # Build display reference mapping
        display_refs = {}
        for displayref in back.findall("displayreference"):
            target = displayref.get("target", "")
            to = displayref.get("to", "")
            if target and to:
                display_refs[target] = to

        # Process references - check if there's a parent <references> wrapper
        references_parent = back.find("references")
        if references_parent is not None:
            # Single references section with subsections
            parent_name = references_parent.find("name")
            parent_anchor = references_parent.get("anchor", "references")

            self.markdown_lines.append(f'<a name="{parent_anchor}"></a>')
            if parent_name is not None and parent_name.text:
                self.markdown_lines.append(f"# {parent_name.text}")
            else:
                self.markdown_lines.append("# References")
            self.markdown_lines.append("")

            # Process subsections (Normative/Informative)
            for ref_section in references_parent.findall("references"):
                name_elem = ref_section.find("name")
                if name_elem is not None and name_elem.text:
                    anchor = ref_section.get("anchor", "")
                    if anchor:
                        self.markdown_lines.append(f'<a name="{anchor}"></a>')
                    self.markdown_lines.append(f"## {name_elem.text}")
                    self.markdown_lines.append("")

                # Process individual references
                for reference in ref_section.findall("reference"):
                    self._process_reference(reference, display_refs)

        # Process appendices and other sections in back
        for section in back.findall("section"):
            # Check if it's a special section (Acknowledgements, Contributors, Authors' Addresses)
            anchor = section.get("anchor", "")
            numbered = section.get("numbered", "true")

            # These sections are typically unnumbered
            if numbered == "false" or anchor in [
                "Acknowledgements",
                "acknowledgements",
                "Contributors",
                "contributors",
                "authors-addresses",
            ]:
                self._process_unnumbered_section(section)
            else:
                self._process_section(section, depth=1)

    def _process_unnumbered_section(self, section):
        """
        Process unnumbered sections like Acknowledgements, Contributors, Authors' Addresses.

        Args:
            section: XML section element
        """
        # Extract section name
        name_elem = section.find("name")
        if name_elem is not None and name_elem.text:
            anchor = section.get("anchor", "")

            # Add anchor if present
            if anchor:
                self.markdown_lines.append(f'<a name="{anchor}"></a>')

            self.markdown_lines.append(f"# {name_elem.text}")
            self.markdown_lines.append("")

        # Process content - could be paragraphs, contacts, authors, etc.
        for child in section:
            if child.tag == "t":
                # Paragraph
                text = self._get_element_text(child)
                if text:
                    self.markdown_lines.append(text)
                    self.markdown_lines.append("")
            elif child.tag == "contact":
                # Contact information (for Contributors)
                self._process_contact(child)
            elif child.tag == "author":
                # Author information (for Authors' Addresses)
                self._process_author_address(child)

    def _process_author_address(self, author_elem):
        """
        Process author element for Authors' Addresses section.

        Args:
            author_elem: XML author element
        """
        fullname = author_elem.get("fullname", "")
        initials = author_elem.get("initials", "")
        surname = author_elem.get("surname", "")

        # Display name
        if fullname:
            self.markdown_lines.append(f"**{fullname}**")
        elif initials and surname:
            self.markdown_lines.append(f"**{initials} {surname}**")
        elif surname:
            self.markdown_lines.append(f"**{surname}**")

        self.markdown_lines.append("")

        # Organization
        org = author_elem.find("organization")
        if org is not None and org.text:
            self.markdown_lines.append(f"- Organization: {org.text}")

        # Address
        address = author_elem.find("address")
        if address is not None:
            # Postal address
            postal = address.find("postal")
            if postal is not None:
                street = postal.find("street")
                city = postal.find("city")
                region = postal.find("region")
                code = postal.find("code")
                country = postal.find("country")

                address_parts = []
                if street is not None and street.text:
                    address_parts.append(street.text)
                if city is not None and city.text:
                    address_parts.append(city.text)
                if region is not None and region.text:
                    address_parts.append(region.text)
                if code is not None and code.text:
                    address_parts.append(code.text)
                if country is not None and country.text:
                    address_parts.append(country.text)

                if address_parts:
                    self.markdown_lines.append(f"- Address: {', '.join(address_parts)}")

            # Email
            email = address.find("email")
            if email is not None and email.text:
                self.markdown_lines.append(f"- Email: {email.text}")

        self.markdown_lines.append("")

    def _process_contact(self, contact_elem):
        """
        Process contact element for Contributors or Authors' Addresses.

        Args:
            contact_elem: XML contact element
        """
        fullname = contact_elem.get("fullname", "")

        if fullname:
            self.markdown_lines.append(f"**{fullname}**")
            self.markdown_lines.append("")

        # Organization
        org = contact_elem.find("organization")
        if org is not None and org.text:
            self.markdown_lines.append(f"- Organization: {org.text}")

        # Address
        address = contact_elem.find("address")
        if address is not None:
            # Postal address
            postal = address.find("postal")
            if postal is not None:
                street = postal.find("street")
                city = postal.find("city")
                region = postal.find("region")
                code = postal.find("code")
                country = postal.find("country")

                address_parts = []
                if street is not None and street.text:
                    address_parts.append(street.text)
                if city is not None and city.text:
                    address_parts.append(city.text)
                if region is not None and region.text:
                    address_parts.append(region.text)
                if code is not None and code.text:
                    address_parts.append(code.text)
                if country is not None and country.text:
                    address_parts.append(country.text)

                if address_parts:
                    self.markdown_lines.append(f"- Address: {', '.join(address_parts)}")

            # Email
            email = address.find("email")
            if email is not None and email.text:
                self.markdown_lines.append(f"- Email: {email.text}")

        self.markdown_lines.append("")

    def _process_reference(self, reference, display_refs):
        """
        Process a single reference entry.

        Args:
            reference: XML reference element
            display_refs: Dictionary mapping reference anchors to display names
        """
        anchor = reference.get("anchor", "")
        target = reference.get("target", "")

        # Use display reference if available
        ref_id = display_refs.get(anchor, anchor)

        # Extract reference information
        front = reference.find("front")
        if front is None:
            return

        ref_parts = []

        # Add reference ID
        if ref_id:
            ref_parts.append(f'<a name="{anchor}"></a>')
            ref_parts.append(f"**[{ref_id}]**")

        # Extract authors
        authors = front.findall("author")
        author_names = []
        for author in authors:
            initials = author.get("initials", "")
            surname = author.get("surname", "")
            fullname = author.get("fullname", "")

            if surname:
                if initials:
                    author_names.append(f"{initials} {surname}")
                else:
                    author_names.append(surname)
            elif fullname:
                author_names.append(fullname)

        if author_names:
            ref_parts.append(", ".join(author_names) + ",")

        # Extract title
        title_elem = front.find("title")
        if title_elem is not None and title_elem.text:
            ref_parts.append(f'"{title_elem.text}",')

        # Extract seriesInfo
        series_infos = reference.findall("seriesInfo")
        series_parts = []
        for series in series_infos:
            name = series.get("name", "")
            value = series.get("value", "")
            if name and value:
                series_parts.append(f"{name} {value}")

        if series_parts:
            ref_parts.append(", ".join(series_parts) + ",")

        # Extract date
        date_elem = front.find("date")
        if date_elem is not None:
            month = date_elem.get("month", "")
            year = date_elem.get("year", "")
            date_str = ""
            if month:
                date_str = f"{month} "
            if year:
                date_str += year
            if date_str:
                ref_parts.append(date_str + ".")

        # Extract refcontent (additional info like "Work in Progress")
        refcontent = reference.find("refcontent")
        if refcontent is not None and refcontent.text:
            ref_parts.append(refcontent.text)

        # Add target URL if available
        if target:
            ref_parts.append(f"<{target}>")

        # Combine all parts
        ref_text = " ".join(ref_parts)
        self.markdown_lines.append(ref_text)
        self.markdown_lines.append("")

    def _process_section(self, section, depth=1):
        """
        Process a section recursively.

        Args:
            section: XML section element
            depth: Current nesting depth (1-6 for Markdown headers)
        """
        # Limit depth to 6 (Markdown maximum)
        depth = min(depth, 6)

        # Extract section name
        name_elem = section.find("name")
        if name_elem is not None and name_elem.text:
            header_prefix = "#" * depth
            anchor = section.get("anchor", "")

            # Add anchor if present
            if anchor:
                self.markdown_lines.append(f'<a name="{anchor}"></a>')

            self.markdown_lines.append(f"{header_prefix} {name_elem.text}")
            self.markdown_lines.append("")

        # Process all child elements in order
        for child in section:
            if child.tag == "t":
                # Paragraph
                text = self._get_element_text(child)
                if text:
                    indent = child.get("indent", "0")
                    if indent != "0":
                        text = "  " * int(indent) + text
                    self.markdown_lines.append(text)
                    self.markdown_lines.append("")
            elif child.tag == "ul":
                # Unordered list
                self._process_list(child, ordered=False)
            elif child.tag == "ol":
                # Ordered list
                self._process_list(child, ordered=True)
            elif child.tag == "dl":
                # Definition list
                self._process_definition_list(child)
            elif child.tag == "figure":
                # Figure with artwork or sourcecode
                self._process_figure(child)
            elif child.tag == "artwork":
                # Standalone artwork
                self._process_artwork(child)
            elif child.tag == "sourcecode":
                # Standalone sourcecode
                self._process_sourcecode(child)
            elif child.tag == "table":
                # Table
                self._process_table(child)
            elif child.tag == "note":
                # Note (blockquote)
                self._process_note(child)
            elif child.tag == "section":
                # Nested section
                self._process_section(child, depth + 1)

    def _process_list(self, list_elem, ordered=False, indent_level=0):
        """
        Process unordered or ordered lists.

        Args:
            list_elem: XML list element (ul or ol)
            ordered: True for ordered lists, False for unordered
            indent_level: Current indentation level for nested lists
        """
        indent = "  " * indent_level
        counter = 1

        for li in list_elem.findall("li"):
            # Get list item text
            text = self._get_element_text(li)

            if ordered:
                prefix = f"{counter}."
                counter += 1
            else:
                prefix = "-"

            if text:
                self.markdown_lines.append(f"{indent}{prefix} {text}")

            # Handle nested lists
            for child in li:
                if child.tag == "ul":
                    self._process_list(child, ordered=False, indent_level=indent_level + 1)
                elif child.tag == "ol":
                    self._process_list(child, ordered=True, indent_level=indent_level + 1)

        if indent_level == 0:
            self.markdown_lines.append("")

    def _process_definition_list(self, dl_elem):
        """Process definition lists."""
        for child in dl_elem:
            if child.tag == "dt":
                # Definition term
                term = self._get_element_text(child)
                if term:
                    self.markdown_lines.append(f"**{term}**")
            elif child.tag == "dd":
                # Definition description - can contain text, paragraphs, figures, nested lists
                # Check for nested structural elements
                has_nested_elements = any(
                    subchild.tag in ["t", "figure", "ul", "ol", "dl", "artwork", "sourcecode"]
                    for subchild in child
                )

                if has_nested_elements:
                    # Process nested elements
                    for subchild in child:
                        if subchild.tag == "t":
                            text = self._get_element_text(subchild)
                            if text:
                                # Indent paragraphs in dd
                                for line in text.split("\n"):
                                    if line.strip():
                                        self.markdown_lines.append(f"  {line}")
                                self.markdown_lines.append("")
                        elif subchild.tag == "figure":
                            # Process nested figure with indentation
                            saved_lines = self.markdown_lines[:]
                            self.markdown_lines = []
                            self._process_figure(subchild)
                            # Indent all figure lines
                            for line in self.markdown_lines:
                                saved_lines.append(f"  {line}" if line else "")
                            self.markdown_lines = saved_lines
                        elif subchild.tag in ["ul", "ol"]:
                            self._process_list(
                                subchild, ordered=(subchild.tag == "ol"), indent_level=1
                            )
                        elif subchild.tag == "dl":
                            # Nested definition list - indent it
                            saved_lines = self.markdown_lines[:]
                            self.markdown_lines = []
                            self._process_definition_list(subchild)
                            for line in self.markdown_lines:
                                saved_lines.append(f"  {line}" if line else "")
                            self.markdown_lines = saved_lines
                else:
                    # Simple text content
                    desc = self._get_element_text(child)
                    if desc:
                        # Indent the description
                        for line in desc.split("\n"):
                            if line.strip():
                                self.markdown_lines.append(f"  {line}")
                        self.markdown_lines.append("")

        self.markdown_lines.append("")

    def _process_figure(self, figure_elem):
        """Process figure elements containing artwork or sourcecode."""
        # Get figure number from pn attribute (e.g., "figure-8" -> "8")
        pn = figure_elem.get("pn", "")
        figure_num = ""
        if pn.startswith("figure-"):
            figure_num = pn.replace("figure-", "") + ": "

        # Get figure name if present
        name_elem = figure_elem.find("name")
        if name_elem is not None and name_elem.text:
            if figure_num:
                self.markdown_lines.append(f"**Figure {figure_num}{name_elem.text}**")
            else:
                self.markdown_lines.append(f"**Figure: {name_elem.text}**")
            self.markdown_lines.append("")

        # Process artwork or sourcecode within figure
        for child in figure_elem:
            if child.tag == "artwork":
                self._process_artwork(child, in_figure=True)
            elif child.tag == "sourcecode":
                self._process_sourcecode(child, in_figure=True)

    def _process_artwork(self, artwork_elem, in_figure=False):
        """Process artwork elements (ASCII art, diagrams)."""
        # Get artwork content
        content = artwork_elem.text or ""

        # Preserve exact formatting with code block
        self.markdown_lines.append("```")
        if content:
            # Split by lines and preserve whitespace
            for line in content.split("\n"):
                self.markdown_lines.append(line.rstrip())
        self.markdown_lines.append("```")

        if not in_figure:
            self.markdown_lines.append("")

    def _process_sourcecode(self, sourcecode_elem, in_figure=False):
        """Process sourcecode elements."""
        # Get language type if specified
        lang = sourcecode_elem.get("type", "")

        # Get sourcecode content
        content = sourcecode_elem.text or ""

        # Create code block with language specification
        if lang:
            self.markdown_lines.append(f"```{lang}")
        else:
            self.markdown_lines.append("```")

        if content:
            for line in content.split("\n"):
                self.markdown_lines.append(line.rstrip())

        self.markdown_lines.append("```")

        if not in_figure:
            self.markdown_lines.append("")

    def _process_table(self, table_elem):
        """Process table elements."""
        # Extract table name if present
        name_elem = table_elem.find("name")
        if name_elem is not None and name_elem.text:
            self.markdown_lines.append(f"**Table: {name_elem.text}**")
            self.markdown_lines.append("")

        # Process thead for headers
        thead = table_elem.find("thead")
        headers = []
        if thead is not None:
            tr = thead.find("tr")
            if tr is not None:
                for th in tr.findall("th"):
                    headers.append(self._get_element_text(th) or "")

        # Process tbody for data rows
        tbody = table_elem.find("tbody")
        rows = []
        if tbody is not None:
            for tr in tbody.findall("tr"):
                row = []
                for td in tr.findall("td"):
                    row.append(self._get_element_text(td) or "")
                if row:
                    rows.append(row)

        # Generate Markdown table
        if headers:
            # Header row
            self.markdown_lines.append("| " + " | ".join(headers) + " |")
            # Separator row
            self.markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        # Data rows
        for row in rows:
            # Pad row to match header length if needed
            while len(row) < len(headers):
                row.append("")
            self.markdown_lines.append("| " + " | ".join(row) + " |")

        self.markdown_lines.append("")

    def _process_note(self, note_elem):
        """Process note elements as blockquotes."""
        # Get note name if present
        name_elem = note_elem.find("name")
        if name_elem is not None and name_elem.text:
            self.markdown_lines.append(f"> **{name_elem.text}**")
            self.markdown_lines.append(">")

        # Process paragraphs in note
        for t_elem in note_elem.findall("t"):
            text = self._get_element_text(t_elem)
            if text:
                # Prefix each line with >
                for line in text.split("\n"):
                    if line.strip():
                        self.markdown_lines.append(f"> {line}")
                self.markdown_lines.append(">")

        self.markdown_lines.append("")

    def _get_element_text(self, elem):
        """
        Extract text content from an element, handling inline elements.

        Args:
            elem: XML element

        Returns:
            String with text content
        """
        if elem is None:
            return ""

        # Get all text including from child elements
        text_parts = []

        # Add initial text
        if elem.text:
            text_parts.append(elem.text)

        # Process child elements
        for child in elem:
            # Handle inline formatting
            if child.tag == "xref":
                # Cross-references
                target = child.get("target", "")
                derived_content = child.get("derivedContent", "")
                child_text = child.text or derived_content or target

                # Create internal link
                if target.startswith("#"):
                    text_parts.append(f"[{child_text}]({target})")
                else:
                    text_parts.append(f"[{child_text}](#{target})")

            elif child.tag == "eref":
                # External references
                target = child.get("target", "")
                child_text = child.text or target
                text_parts.append(f"[{child_text}]({target})")

            elif child.tag == "bcp14":
                # BCP14 keywords (MUST, SHOULD, etc.) - make bold
                child_text = child.text or ""
                text_parts.append(f"**{child_text}**")

            elif child.tag == "em":
                # Emphasis - italic
                child_text = child.text or ""
                text_parts.append(f"*{child_text}*")

            elif child.tag == "strong":
                # Strong - bold
                child_text = child.text or ""
                text_parts.append(f"**{child_text}**")

            elif child.tag == "tt":
                # Teletype - inline code
                child_text = child.text or ""
                text_parts.append(f"`{child_text}`")

            elif child.tag == "contact":
                # Contact - use fullname attribute if available, otherwise text
                fullname = child.get("fullname", "")
                child_text = fullname or child.text or ""
                text_parts.append(child_text)

            else:
                # Default: recursively get text from child
                child_text = self._get_element_text(child)
                if child_text:
                    text_parts.append(child_text)

            # Add tail text
            if child.tail:
                text_parts.append(child.tail)

        return "".join(text_parts).strip()
