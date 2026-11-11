import asyncio
import subprocess
import sys
import time

import pytest

import barebidi as nb
from barebidi.browser import _is_snap

NEVER = "new Promise(() => {})"


async def test_command_times_out_and_the_connection_stays_usable(server):
    async with nb.Browser(headless=True, timeout=1) as browser:
        tab = await browser.get(f"{server}/index.html")
        started = time.monotonic()
        with pytest.raises(TimeoutError, match="script.evaluate"):
            await tab.evaluate(NEVER)
        assert time.monotonic() - started < 3
        assert await tab.evaluate("1 + 1") == 2


async def test_navigation_timeout(tab, server):
    with pytest.raises(TimeoutError):
        await tab.get(f"{server}/hang?seconds=5", timeout=1)


async def test_input_outlasts_the_command_timeout(server):
    # Typing is one command that lasts as long as the typing: the timeout counts on top of it.
    async with nb.Browser(headless=True, timeout=1) as browser:
        tab = await browser.get(f"{server}/index.html")
        field = await tab.select("#name")
        await field.type("una frase bastante larga")
        assert await field.get_property("value") == "una frase bastante larga"


async def test_crash_fails_pending_and_later_commands(server):
    browser = await nb.Browser(headless=True).start()
    try:
        tab = await browser.get(f"{server}/index.html")
        pending = asyncio.create_task(tab.evaluate(NEVER))
        await asyncio.sleep(0.3)
        browser._process.kill()  # a crash
        with pytest.raises(nb.BrowserClosedError):
            await asyncio.wait_for(pending, 10)
        with pytest.raises(nb.BrowserClosedError):
            await tab.evaluate("1")
    finally:
        await asyncio.wait_for(browser.stop(), 10)


def test_snap_firefox_is_recognised(tmp_path):
    # Ubuntu's /usr/bin/firefox is a script that runs the snap, whose /tmp is private: our temporary
    # profile has to live where the snap can reach it.
    wrapper = tmp_path / "firefox"
    wrapper.write_text("#!/bin/sh\nexec /snap/bin/firefox \"$@\"\n")
    assert _is_snap(str(wrapper))
    assert not _is_snap(sys.executable)


@pytest.mark.skipif(sys.platform == "win32", reason="the fake Firefox is a shell script")
async def test_firefox_restarting_itself_at_startup(tmp_path, server):
    # Right after an update, Firefox may restart itself to finish it: the process we started exits and an
    # orphan copy carries on with our profile. We must not leave it behind, and should try once more.
    fake = tmp_path / "firefox"
    fake.write_text(
        "#!/bin/sh\n"
        f'if [ ! -e "{tmp_path}/restarted" ]; then touch "{tmp_path}/restarted"; "{nb.find_firefox()}" "$@" >/dev/null 2>&1 & exit 0; fi\n'
        f'exec "{nb.find_firefox()}" "$@"\n'
    )
    fake.chmod(0o755)
    async with nb.Browser(headless=True, executable_path=str(fake)) as browser:
        tab = await browser.get(f"{server}/index.html")
        assert await tab.title()
        profile = browser._profile
        assert len(_firefoxes_using(profile)) == 1  # the orphan is gone, only ours runs
    assert _firefoxes_using(profile) == []


def _firefoxes_using(profile: str) -> list[str]:
    """Main Firefox processes launched on `profile` (not their content processes)."""
    listing = subprocess.run(["ps", "-A", "-ww", "-o", "pid=,command="], capture_output=True, text=True).stdout
    return [line.split(None, 1)[0] for line in listing.splitlines() if f"--remote-debugging-port=0 --profile {profile}" in line]
