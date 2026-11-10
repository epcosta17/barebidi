# Linux with Firefox, for running nodriver-bidi (and its tests) the way scrapers run on servers.
#
#   docker build -t nodriver-bidi .
#   docker run --rm --shm-size=2g nodriver-bidi                 # the test suite
#   docker run --rm --shm-size=2g nodriver-bidi uv run python your_script.py
#
# Firefox needs more shared memory than Docker's default 64 MB, hence --shm-size.
#
# Everything runs on a virtual 1920x1080 screen, so Browser(headless=False) works too, and on Linux it is the
# better choice: headless Firefox there gets no WebGL at all, and detectors find it less like a desktop.
FROM python:3.12-slim-bookworm

# Firefox from Mozilla's own APT repository: the current release, not Debian's ESR. Fonts, because a
# machine with almost none is easy to tell apart from a desktop; Mesa, because without a GPU or a
# software renderer there is no WebGL at all, which no real browser lacks.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
 && install -d -m 0755 /etc/apt/keyrings \
 && curl -fsSL https://packages.mozilla.org/apt/repo-signing-key.gpg -o /etc/apt/keyrings/packages.mozilla.org.asc \
 && echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" > /etc/apt/sources.list.d/mozilla.list \
 && printf 'Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1000\n' > /etc/apt/preferences.d/mozilla \
 && apt-get update \
 && apt-get install -y --no-install-recommends firefox fonts-liberation fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
      libgl1-mesa-dri libegl1 libgl1 xvfb xauth tini \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /usr/local/bin/uv

RUN useradd --create-home scraper
USER scraper
WORKDIR /home/scraper/app

COPY --chown=scraper pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY --chown=scraper . .
RUN uv sync --frozen

# tini, because xvfb-run hangs when it is the container's first process.
ENTRYPOINT ["tini", "--", "xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24"]
CMD ["uv", "run", "pytest", "-q"]
