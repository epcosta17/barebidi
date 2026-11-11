# Dialogs, uploads and downloads

## Dialogs

`alert()`, `confirm()`, `prompt()` and "leave this page?" dialogs never block barebidi. Without a handler
they get Firefox's usual answer: alerts and "leave this page?" accepted, confirms and prompts dismissed. With
`humanize` on, every answer comes after the time a person would take to read the dialog and type.

To answer them yourself:

```python
async def answer(dialog):
    # dialog.type: "alert", "confirm", "prompt" or "beforeunload"
    print(dialog.type, dialog.message)
    if dialog.type == "prompt":
        await dialog.accept("Ana")
    else:
        await dialog.dismiss()

# this tab only; browser.on_dialog() for every tab
stop = await tab.on_dialog(answer)
...
stop()
```

`dialog.default_value` holds a prompt's prefilled text.

## Uploads

```python
await tab.select("input[type=file]").set_files("report.pdf")
await tab.select("input[type=file][multiple]").set_files("a.jpg", "b.jpg")
```

## Downloads

```python
async with tab.expect_download() as expected:
    await tab.find("Export CSV").click()
path = await expected.download.path()   # waits for the whole file
print(path.read_text())
```

Files go to a temporary folder, deleted when the browser stops, unless you choose one:
`Browser(downloads="/path/to/downloads")`.
