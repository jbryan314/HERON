from typing import Any
import xml.etree.ElementTree as ET

from ..xml_utils import _to_string


class RavenSnippet(ET.Element):
  """
  RavenSnippet class objects describe one contiguous snippet of RAVEN XML, inheriting from the xml.etree.ElementTree.Element
  class. This base class contains methods for quickly building subtrees and set and access common RAVEN node attributes.
  """
  # TODO: alternative constructor using existing node from template?

  def __init__(self,
               tag: str,
               name: str | None = None,
               class_name: str | None = None,
               subtype_name: str | None = None,
               subelements: dict[str, Any] = {},
               **kwargs) -> None:
    """
    @ In, name, str, the name of the entity
    @ In, class_name, str, the name of the class the entity belongs too (e.g. Models, Optimizers, DataObjects)
    @ In, type_name, str, the entity's type (e.g. Code, ROM, PointSet)
    @ In, subtype_name, str, optional, the entity's subtype (e.g. RAVEN as a subtype of Code)
    @ In, subelements, dict[str, Any], optional, keyword settings which are added as XML child nodes
    @ In, kwargs, dict, optional, additional keyword arguments added to the Element attributes
    @ Out, None
    """
    super().__init__(tag)

    # Update node attributes with provided values
    # Arguments "name", "class_name", and "subtype_name" help to alias the problematic "class" attribute name and provide
    # an easy interface to set the common attributes "name" and "subType".
    if name is not None:
      self.attrib["name"] = name
    if subtype_name is not None:
      self.attrib["subType"] = subtype_name
    self.attrib.update(kwargs)

    # The snippet class is not typically one of the XML node attributes. However, it's useful to hold onto this
    # information since this can tell us where in the XML snippet belongs and helps us construct an assmbler node
    # from the snippet.
    self._class = class_name

    self.add_subelements(subelements)

  def __repr__(self) -> str:
    """
    Make a string representation of the snippet. If the "name" attribute is defined, return that. Otherwise, fall back
    to the ET.Element implementation.
    """
    if name := self.name:
      return name
    return super().__repr__()

  @classmethod
  def from_xml(cls, node: ET.Element) -> "RavenSnippet":
    """
    Alternate constructor which instantiates a new RavenSnippet object from an existing XML node
    @ In, node, ET.Element, the template node
    @ Out, snippet, RavenSnippet, the new snippet
    """
    # Default implementation is to copy everything from the existing node into a new RavenSnippet object.
    # Note that the snippet_class attribute does not show up in the XML, so subclasses relying on this
    # default implementation will not have that attribute set.
    snippet = cls(node.tag)
    snippet.attrib.update(node.attrib)
    snippet.text = node.text
    for child in node:
      snippet.append(child)
    return snippet

  # Attribute getters
  # NOTE: Using properties would be more pythonic, but the unfortunate naming of the "class" attribute for RAVEN nodes
  # leads to issues with a property like "snippet.class" conflicting with the protected keyword "class".
  @property
  def name(self) -> str:
    return self.attrib.get("name", "")

  @property
  def snippet_class(self) -> str | None:
    return self._class

  @property
  def type(self) -> str:
    return self.tag

  @property
  def subtype(self) -> str:
    return self.attrib.get("subType", "")

  def get_name(self) -> str:
    return self.attrib.get("name", "")

  def get_class(self) -> str | None:
    return self._class

  def get_type(self) -> str:
    return self.tag

  def get_subtype(self) -> str | None:
    return self.attrib.get("subType", None)

  def add_subelements(self, subelements: dict[str, Any] = {}, **kwargs) -> None:
    """
    Add subelements by either providing a dict or keyword arguments.
    @ In, subelements, dict[str, Any], optional, dict with new key-value settings pairs
    @ In, kwargs, dict, optional, new settings provided as keyword arguments
    @ Out, None
    """
    parent = kwargs.pop("parent", self)
    for tag, value in (subelements | kwargs).items():
      self._add_subelement(parent, tag, value)

  def _add_subelement(self, parent: ET.Element, tag: str, value: Any) -> None:
    """
    Recursively build out subtree. Recurse over dicts, set child node text to string or numeric values,
    or form comma separated lists for other iterative data types (list, numpy array, tuple, set, etc.).
    @ In, parent, ET.Element, the parent node to append to
    @ In, tag, str, the tag of the child node
    @ In, value, Any, the value of the child node
    """
    # If the value inherits from ET.Element, we can append the value to the parent directly.
    if isinstance(value, ET.Element):
      parent.append(value)
    # If the value happens to be another entity, it has its own to_xml method. Use that instead of manually
    # using the tag input to create the child node.
    elif isinstance(value, RavenSnippet):
      # has a to_xml method
      child = value.to_xml()
      parent.append(child)
    # Otherwise, we'll create the child node ourselves. We handle several possible types of value:
    #   1. If value is a dict, create an XML subtree using the dict key-value pairs.
    #   2. If the value is iterable but not a string (so a list, numpy array, tuple, set, etc.), create a
    #      comma separated list of the values and set the node's text to that.
    #   3. If the value is anything else (assumes can be cast to a reasonable string), just set the node
    #      text to that value.
    else:
      child = ET.SubElement(parent, tag)
      if isinstance(value, dict):
        for tag, value in value.items():
          self._add_subelement(child, tag, value)
      else:
        child.text = _to_string(value)

  # Other utility functions
  def to_assembler_node(self, tag: str) -> ET.Element:
    """
    Creates an assembler node from the snippet, if possible. The "class" attribute must be defined.
    @ In, tag, str, assembler node tag
    """
    if not (self.snippet_class and self.name):
      raise ValueError("The RavenSnippet object cannot be expressed as an Assembler node! The object must have "
                       "'name' and 'class' attributes defined to create an Assembler node. Current values: "
                       f"class='{self.snippet_class}', name='{self.name}'.")

    node = ET.Element(tag)
    node.attrib["class"] = self.snippet_class
    node.attrib["type"] = self.type
    node.text = self.name

    return node
