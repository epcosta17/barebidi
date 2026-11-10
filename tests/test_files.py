import pytest

import nodriver_bidi as nb

CSV = "a,b\n1,2\n"


@pytest.fixture
async def page(browser, server):
    return await browser.get(f"{server}/files.html")


async def test_set_files(page, tmp_path):
    first, second = tmp_path / "uno.txt", tmp_path / "dos.txt"
    first.write_text("primero")
    second.write_text("segundo")
    await (await page.select("#file")).set_files(first, second)
    assert await page.evaluate("contents()") == [["uno.txt", "primero"], ["dos.txt", "segundo"]]
    assert ["change", True] in await page.evaluate("events")


async def test_set_files_checks_the_paths(page, tmp_path):
    with pytest.raises(FileNotFoundError):
        await (await page.select("#file")).set_files(tmp_path / "missing.txt")


async def test_clicking_a_file_input_opens_no_picker(page):
    # A native file dialog would block the automation; it is cancelled at once instead.
    await (await page.select("#file")).click()
    assert ["cancel", True] in await page.evaluate("events")


async def test_expect_download(page):
    async with page.expect_download() as expected:
        await (await page.select("#csv")).click()
    download = expected.download
    assert download.suggested_filename == "report.csv"
    assert download.url.endswith("/download?name=report.csv")
    assert (await download.path()).read_text() == CSV


async def test_save_download_as(page, tmp_path):
    async with page.expect_download() as expected:
        await (await page.select("#csv")).click()
    saved = await expected.download.save_as(tmp_path / "copia.csv")
    assert saved == tmp_path / "copia.csv" and saved.read_text() == CSV


async def test_downloads_folder(server, tmp_path):
    async with nb.Browser(headless=True, downloads=tmp_path) as browser:
        tab = await browser.get(f"{server}/files.html")
        async with tab.expect_download() as expected:
            await (await tab.select("#csv")).click()
        assert (await expected.download.path()).parent == tmp_path


async def test_temporary_downloads_go_away_with_the_browser(server):
    async with nb.Browser(headless=True) as browser:
        tab = await browser.get(f"{server}/files.html")
        async with tab.expect_download() as expected:
            await (await tab.select("#csv")).click()
        path = await expected.download.path()
        assert path.exists()
    assert not path.exists()


async def test_expect_download_times_out(page):
    with pytest.raises(TimeoutError):
        async with page.expect_download(timeout=0.5):
            pass
