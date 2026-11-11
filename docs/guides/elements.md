# Finding elements

## Three ways to look

```python
button = await tab.select("form button[type=submit]")    # CSS
link = await tab.find("Learn more")                       # by visible text
rows = await tab.xpath("//table//tr[td]")                  # XPath, always a list
items = await tab.select_all(".item")                      # CSS, a list
```

All of them **wait** until something matches, 10 seconds by default; `timeout=` changes it. If nothing shows
up in time, `select()` and `find()` raise `TimeoutError`, and `select_all()` and `xpath()` return an empty
list.

`find(text)` returns the first element whose own text contains `text`, ignoring case.
`find(text, exact=True)` wants its text to equal `text`.

## Chaining

`select()` and `find()` return a query you can act on directly, without awaiting the element first:

```python
await tab.select("#email").type("me@example.com")
await tab.select("form").select("button").click()
print(await tab.select("h1").text())
```

The lookup happens when you await the action, so the element is fetched fresh, right before it is used.
Await the query itself to get the element:

```python
card = await tab.select(".card")
title = await card.select("h2").text()
link = await card.select("a").get_attribute("href")
```

## Reading

```python
await element.text()              # textContent
await element.inner_text()        # the text as rendered
await element.html()              # outerHTML
await element.get_attribute("href")
await element.get_property("checked")
await element.call("function () { return this.dataset.id }")
```

## Acting

```python
await element.click()
await element.hover()
await element.type("hello")
await element.press("Enter")
await element.clear()
await element.scroll_into_view()
await element.set_files("photo.jpg")   # <input type=file>
```

See [Mouse and keyboard](input.md) for how these move and type.

## The page itself

```python
html = await tab.content()        # the whole document's HTML
url = await tab.url()
title = await tab.title()
```
