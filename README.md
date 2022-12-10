# XMLTaggedPOSSelector
A CSS-selector-like language for XML-Tagged POS querying

# How it works
Selector is converted to XPath (2.0 for regex function)
```
> python3 bastpath.py
a
//a

*
//*

a=b
//a[(((string(.)="b" and string(..)!=string(.))))]

a..=b
//*[((starts-with(name(), "a")) and ((string(.)="b" and string(..)!=string(.))))]

..a=b
//*[((ends-with(name(), "a")) and ((string(.)="b" and string(..)!=string(.))))]

..a..,b=c
//*[((contains(name(), "a") or name()="b") and ((string(.)="c" and string(..)!=string(.))))]

/x/i,b=c
//*[((matches(name(), "x", "i") or name()="b") and ((string(.)="c" and string(..)!=string(.))))]

a=..b
//a[(((ends-with(string(.), "b") and string(..)!=string(.))))]

..a=..b
//*[((ends-with(name(), "a")) and ((ends-with(string(.), "b") and string(..)!=string(.))))]

a=b..
//a[(((starts-with(string(.), "b") and string(..)!=string(.))))]

a=..b..
//a[(((contains(string(.), "b") and string(..)!=string(.))))]

a=!..b..
//a[((not((contains(string(.), "b") and string(..)!=string(.)))))]

!a=b
//a[(((string(.)="b" and string(..)!=string(.))))]

a,b=c
//*[((name()="a" or name()="b") and ((string(.)="c" and string(..)!=string(.))))]

a b c
//a//b//c

a>b > c
//a/b/c

a b>b,c,!d, e
//a//b/*[((name()="b" or name()="c" or name()!="d" or name()="e"))]

a b=/x/
//a//b[(((matches(string(.), "x") and string(..)!=string(.))))]

```
# TODO
* String escaping
