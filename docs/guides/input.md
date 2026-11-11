# Mouse and keyboard

barebidi sends input as real mouse and keyboard events through Firefox, not as JavaScript calls such as
`element.click()`. With `humanize=True` (the default) they also move and time like a person.

## Clicking and hovering

`click()` and `hover()`:

1. scroll the element into view with the mouse wheel, in notches with pauses, if it is off screen;
2. aim at a point of the element that nothing else covers, near its center but rarely right on it;
3. move the mouse there from wherever the pointer was, along a path a hand would take (see below);
4. check the pointer really is over the element, and aim again if the page moved it meanwhile;
5. for `click()`, press and release the button with a short hold.

```python
await tab.select("#menu").hover()
await tab.find("Settings").click()
```

## Recorded movements

By default barebidi generates each mouse path: a curve that speeds up and slows down, with a duration that
depends on distance and target size, a slight tremor and an occasional overshoot.

Install the optional [Cursory](https://github.com/Vinyzu/cursory) package and it replays movements recorded
from real people instead. Cursory holds over two thousand of them; for each move it picks one that suits the
direction and distance and fits it to the start and end points, keeping the hand's own timing, hesitations
and corrections. Generated curves are smooth in ways hands are not, which classifiers can pick up.

```
pip install "barebidi[cursory]"
```

Nothing else changes: barebidi uses it whenever it is installed. Cursory is LGPL-3.0 and depends on numpy;
barebidi itself stays MIT and dependency-light without it.

## Typing

```python
await tab.select("#search").type("Firefox BiDi")
await tab.select("#search").press("Enter")
await tab.select("#search").clear()
```

`type()` clicks the field first, then types character by character with varying hold and pause times,
holding Shift for capitals and symbols like a keyboard would. `press()` takes one character or a key name:
`Enter`, `Tab`, `Backspace`, `Escape`, `Delete`, `ArrowLeft`, `ArrowUp`, `ArrowRight`, `ArrowDown`.
`clear()` selects the field's content and deletes it.

## Scrolling

```python
await tab.scroll(800)    # down 800 px with the wheel, where the pointer is
await tab.scroll(-400)   # up

# jump straight to an element, without wheel events
await element.scroll_into_view()
```

## Turning it off

`Browser(humanize=False)` keeps real input events but drops the delays and curves: straight moves and
immediate clicks and keystrokes. Useful for tests and when speed matters more than looking human.

## Inside iframes

Clicks and typing reach elements inside iframes, cross-site ones included: the mouse moves through the
page like a real one would. See [Iframes and shadow roots](frames.md).
