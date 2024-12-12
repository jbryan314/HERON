class ListWrapper(list):
  """
  A wrapper class which emulates a list (and subclasses list for duck typing) which interfaces with a property
  """
  def __init__(self, property_instance, obj):
    self.property_instance = property_instance
    self.obj = obj

  def _get_list(self):
    return self.property_instance.fget(self.obj)

  def _set_list(self, value):
    self.property_instance.fset(self.obj, value)

  def __getitem__(self, index):
    return self._get_list()[index]

  def __setitem__(self, index, value):
    lst = self._get_list()
    lst[index] = value
    self._set_list(lst)

  def __delitem__(self, index):
    lst = self._get_list()
    del lst[index]
    self._set_list(lst)

  def append(self, object):
    lst = self._get_list()
    lst.append(object)
    self._set_list(lst)

  def extend(self, iterable):
    lst = self._get_list()
    lst.extend(iterable)
    self._set_list(lst)

  def insert(self, index, object):
    lst = self._get_list()
    lst.insert(index, object)
    self._set_list(lst)

  def remove(self, value):
    lst = self._get_list()
    lst.remove(value)
    self._set_list(lst)

  def pop(self, index=-1):
    return self._get_list().pop(index)

  def clear(self):
    lst = self._get_list()
    lst.clear()
    self._set_list(lst)

  def index(self, value):
    return self._get_list().index(value)

  def count(self, value):
    return self._get_list().count(value)

  def sort(self, *, key=None, reverse=False):
    lst = self._get_list()
    lst.sort(key=key, reverse=reverse)
    self._set_list(lst)

  def reverse(self) -> None:
    lst = self._get_list()
    lst.reverse()
    self._set_list(lst)

  def copy(self):
    return self._get_list().copy()

  def __len__(self):
    return len(self._get_list())

  def __iter__(self):
    return iter(self._get_list())

  def __repr__(self):
    return repr(self._get_list())

  def __eq__(self, other):
    return self._get_list() == other

  def __contains__(self, value):
    return value in self._get_list()


class listproperty:
  """
  A approximation of the built-in "property" function/decorator, with additional logic for getting/setting values
  which are lists (or more precisely, ListWrapper objects) in a way that allows for list operations (e.g. append,
  extend, insert) on the property.
  """
  def __init__(self, fget=None, fset=None, fdel=None, doc=None):
    self.fget = fget
    self.fset = fset
    self.fdel = fdel
    if doc is None and fget is not None:
      doc = fget.__doc__
    self.__doc__ = doc

  def __set_name__(self, owner, name):
      self.__name__ = name

  def __get__(self, obj, objtype=None):
    if obj is None:
      return self
    if self.fget is None:
      raise AttributeError("unreadable attribute")
    value = self.fget(obj)
    if isinstance(value, list):
      return ListWrapper(self, obj)
    return value

  def __set__(self, obj, value):
    if self.fset is None:
      raise AttributeError("can't set attribute")
    if not isinstance(value, list):
      raise TypeError("listproperty setter expects a list value")
    self.fset(obj, value)

  def __delete__(self, obj):
    if self.fdel is None:
      raise AttributeError("can't delete attribute")
    self.fdel(obj)

  def getter(self, fget):
    return type(self)(fget, self.fset, self.fdel, self.__doc__)

  def setter(self, fset):
    return type(self)(self.fget, fset, self.fdel, self.__doc__)

  def deleter(self, fdel):
    return type(self)(self.fget, self.fset, fdel, self.__doc__)