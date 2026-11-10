# The remote agent applies its "recommended" prefs unless the profile already defines them.
# Restore Firefox's normal value for the ones a page can observe.
PREFS = {
    "dom.disable_open_during_load": True,  # popup blocker
}

# navigator.webdriver reads the automation state the parent process shares with content processes.
# Firefox clears it itself when it starts its remote agent for agentic browsing rather than automation;
# clearing it the same way keeps the native getter untouched. Runs in a chrome context, which needs
# --remote-allow-system-access.
CLEAR_AUTOMATION_FLAG = """(() => {
  Services.ppmm.sharedData.set("RemoteAgent:IsBrowserAutomationRunning", false);
  Services.ppmm.sharedData.flush();
})()"""

# Fallback for Firefox versions without that flag. Preload script, runs in every new document before
# the page's own scripts: navigator.webdriver returns false through a getter that keeps the native
# name, length, descriptor, toString() output (also from other frames) and TypeError on a wrong
# receiver. Unlike the flag, it leaves a trace: an extra frame in that TypeError's stack.
HIDE_WEBDRIVER = """() => {
  const apply = Reflect.apply;
  const defineProperty = Object.defineProperty;
  const nativeToString = Function.prototype.toString;
  const weakMapGet = WeakMap.prototype.get;
  const mapGet = Map.prototype.get;

  const original = Object.getOwnPropertyDescriptor(Navigator.prototype, "webdriver");
  if (!original || !original.get) return;

  const getter = new Proxy(original.get, {
    apply(target, self, args) {
      apply(target, self, args);
      return false;
    },
  });
  const toString = new Proxy(nativeToString, {
    apply(target, self, args) {
      const disguise = apply(weakMapGet, disguises, [self]);
      if (disguise !== undefined) return disguise;
      const source = apply(target, self, args);
      if (source !== proxySource) return source;
      try {
        return apply(mapGet, byName, [self.name]) ?? source;
      } catch {
        return source;
      }
    },
  });

  const getterSource = apply(nativeToString, original.get, []);
  const toStringSource = apply(nativeToString, nativeToString, []);
  const proxySource = apply(nativeToString, getter, []);
  const disguises = new WeakMap([[getter, getterSource], [toString, toStringSource]]);
  const byName = new Map([[original.get.name, getterSource], [nativeToString.name, toStringSource]]);

  defineProperty(Navigator.prototype, "webdriver", {...original, get: getter});
  defineProperty(Function.prototype, "toString", {value: toString});
}"""
