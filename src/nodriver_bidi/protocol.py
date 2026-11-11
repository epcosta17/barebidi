"""WebDriver BiDi protocol types, generated from the spec CDDL by tools/bidi_codegen.py.

Source: webref ed/cddl at commit 3b4e4517fdc8e51c06b266093888236e6dbeb529.
Do not edit by hand; regenerate from the spec CDDL. Names keep the spec's, with . and - as _.
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict
class Command(TypedDict):
    id: int
    method: NotRequired[Literal["browser.close"] | Literal["browser.createUserContext"] | Literal["browser.getClientWindows"] | Literal["browser.getUserContexts"] | Literal["browser.removeUserContext"] | Literal["browser.setClientWindowState"] | Literal["browser.setDownloadBehavior"] | Literal["browsingContext.activate"] | Literal["browsingContext.captureScreenshot"] | Literal["browsingContext.close"] | Literal["browsingContext.create"] | Literal["browsingContext.getTree"] | Literal["browsingContext.handleUserPrompt"] | Literal["browsingContext.locateNodes"] | Literal["browsingContext.navigate"] | Literal["browsingContext.print"] | Literal["browsingContext.reload"] | Literal["browsingContext.setBypassCSP"] | Literal["browsingContext.setViewport"] | Literal["browsingContext.startScreencast"] | Literal["browsingContext.stopScreencast"] | Literal["browsingContext.traverseHistory"] | Literal["emulation.setForcedColorsModeThemeOverride"] | Literal["emulation.setGeolocationOverride"] | Literal["emulation.setLocaleOverride"] | Literal["emulation.setMediaFeaturesOverride"] | Literal["emulation.setNetworkConditions"] | Literal["emulation.setScreenOrientationOverride"] | Literal["emulation.setScreenSettingsOverride"] | Literal["emulation.setScriptingEnabled"] | Literal["emulation.setScrollbarTypeOverride"] | Literal["emulation.setTextLayoutModeOverride"] | Literal["emulation.setTimezoneOverride"] | Literal["emulation.setTouchOverride"] | Literal["emulation.setUserAgentOverride"] | Literal["emulation.setViewportMetaOverride"] | Literal["input.performActions"] | Literal["input.releaseActions"] | Literal["input.setFiles"] | Literal["network.addDataCollector"] | Literal["network.addIntercept"] | Literal["network.continueRequest"] | Literal["network.continueResponse"] | Literal["network.continueWithAuth"] | Literal["network.disownData"] | Literal["network.failRequest"] | Literal["network.getData"] | Literal["network.provideResponse"] | Literal["network.removeDataCollector"] | Literal["network.removeIntercept"] | Literal["network.setCacheBehavior"] | Literal["network.setExtraHeaders"] | Literal["script.addPreloadScript"] | Literal["script.callFunction"] | Literal["script.disown"] | Literal["script.evaluate"] | Literal["script.getRealms"] | Literal["script.removePreloadScript"] | Literal["session.end"] | Literal["session.new"] | Literal["session.status"] | Literal["session.subscribe"] | Literal["session.unsubscribe"] | Literal["storage.deleteCookies"] | Literal["storage.getCookies"] | Literal["storage.setCookie"] | Literal["webExtension.install"] | Literal["webExtension.uninstall"]]
    params: NotRequired[EmptyParams | browser_CreateUserContextParameters | EmptyParams | EmptyParams | browser_RemoveUserContextParameters | browser_SetClientWindowStateParameters | browser_SetDownloadBehaviorParameters | browsingContext_ActivateParameters | browsingContext_CaptureScreenshotParameters | browsingContext_CloseParameters | browsingContext_CreateParameters | browsingContext_GetTreeParameters | browsingContext_HandleUserPromptParameters | browsingContext_LocateNodesParameters | browsingContext_NavigateParameters | browsingContext_PrintParameters | browsingContext_ReloadParameters | browsingContext_SetBypassCSPParameters | browsingContext_SetViewportParameters | browsingContext_StartScreencastParameters | browsingContext_StopScreencastParameters | browsingContext_TraverseHistoryParameters | emulation_SetForcedColorsModeThemeOverrideParameters | emulation_SetGeolocationOverrideParameters | emulation_SetLocaleOverrideParameters | emulation_SetMediaFeaturesOverrideParameters | emulation_SetNetworkConditionsParameters | emulation_SetScreenOrientationOverrideParameters | emulation_SetScreenSettingsOverrideParameters | emulation_SetScriptingEnabledParameters | emulation_SetScrollbarTypeOverrideParameters | emulation_SetTextLayoutModeOverrideParameters | emulation_SetTimezoneOverrideParameters | emulation_SetTouchOverrideParameters | emulation_SetUserAgentOverrideParameters | emulation_SetViewportMetaOverrideParameters | input_PerformActionsParameters | input_ReleaseActionsParameters | input_SetFilesParameters | network_AddDataCollectorParameters | network_AddInterceptParameters | network_ContinueRequestParameters | network_ContinueResponseParameters | network_ContinueWithAuthParameters | network_DisownDataParameters | network_FailRequestParameters | network_GetDataParameters | network_ProvideResponseParameters | network_RemoveDataCollectorParameters | network_RemoveInterceptParameters | network_SetCacheBehaviorParameters | network_SetExtraHeadersParameters | script_AddPreloadScriptParameters | script_CallFunctionParameters | script_DisownParameters | script_EvaluateParameters | script_GetRealmsParameters | script_RemovePreloadScriptParameters | EmptyParams | session_NewParameters | EmptyParams | session_SubscribeParameters | session_UnsubscribeParameters | storage_DeleteCookiesParameters | storage_GetCookiesParameters | storage_SetCookieParameters | webExtension_InstallParameters | webExtension_UninstallParameters]

type CommandData = BrowserCommand | BrowsingContextCommand | EmulationCommand | InputCommand | NetworkCommand | ScriptCommand | SessionCommand | StorageCommand | WebExtensionCommand

class EmptyParams(TypedDict):
    pass

type Message = CommandResponse | ErrorResponse | Event

class CommandResponse(TypedDict):
    type: Literal["success"]
    id: int
    result: ResultData

class ErrorResponse(TypedDict):
    type: Literal["error"]
    id: int | None
    error: ErrorCode
    message: str
    stacktrace: NotRequired[str]

type ResultData = BrowserResult | BrowsingContextResult | EmulationResult | InputResult | NetworkResult | ScriptResult | SessionResult | StorageResult | WebExtensionResult

class EmptyResult(TypedDict):
    pass

class Event(TypedDict):
    type: Literal["event"]
    method: NotRequired[Literal["browsingContext.contextCreated"] | Literal["browsingContext.contextDestroyed"] | Literal["browsingContext.domContentLoaded"] | Literal["browsingContext.downloadEnd"] | Literal["browsingContext.downloadWillBegin"] | Literal["browsingContext.fragmentNavigated"] | Literal["browsingContext.historyUpdated"] | Literal["browsingContext.load"] | Literal["browsingContext.navigationAborted"] | Literal["browsingContext.navigationCommitted"] | Literal["browsingContext.navigationFailed"] | Literal["browsingContext.navigationStarted"] | Literal["browsingContext.userPromptClosed"] | Literal["browsingContext.userPromptOpened"] | Literal["input.fileDialogOpened"] | Literal["log.entryAdded"] | Literal["network.authRequired"] | Literal["network.beforeRequestSent"] | Literal["network.fetchError"] | Literal["network.responseCompleted"] | Literal["network.responseStarted"] | Literal["script.message"] | Literal["script.realmCreated"] | Literal["script.realmDestroyed"]]
    params: NotRequired[browsingContext_ContextCreatedParameters | browsingContext_Info | browsingContext_NavigationInfo | browsingContext_DownloadEndParams | browsingContext_DownloadWillBeginParams | browsingContext_NavigationInfo | browsingContext_HistoryUpdatedParameters | browsingContext_NavigationInfo | browsingContext_NavigationInfo | browsingContext_NavigationInfo | browsingContext_NavigationInfo | browsingContext_NavigationInfo | browsingContext_UserPromptClosedParameters | browsingContext_UserPromptOpenedParameters | input_FileDialogInfo | log_Entry | network_AuthRequiredParameters | network_BeforeRequestSentParameters | network_FetchErrorParameters | network_ResponseCompletedParameters | network_ResponseStartedParameters | script_MessageParameters | script_RealmInfo | script_RealmDestroyedParameters]

type EventData = BrowsingContextEvent | InputEvent | LogEvent | NetworkEvent | ScriptEvent

type js_int = int

type js_uint = int

type ErrorCode = Literal["invalid argument", "invalid selector", "invalid session id", "invalid web extension", "move target out of bounds", "no such alert", "no such network collector", "no such element", "no such frame", "no such handle", "no such history entry", "no such intercept", "no such network data", "no such node", "no such request", "no such screencast", "no such script", "no such storage partition", "no such user context", "no such web extension", "session not created", "unable to capture screen", "unable to close browser", "unable to set cookie", "unable to set file input", "unavailable network data", "underspecified storage partition", "unknown command", "unknown error", "unsupported operation"]

type SessionCommand = session_End | session_New | session_Status | session_Subscribe | session_Unsubscribe

type SessionResult = session_EndResult | session_NewResult | session_StatusResult | session_SubscribeResult | session_UnsubscribeResult

class session_CapabilitiesRequest(TypedDict):
    alwaysMatch: NotRequired[session_CapabilityRequest]
    firstMatch: NotRequired[list[session_CapabilityRequest]]

class session_CapabilityRequest(TypedDict):
    acceptInsecureCerts: NotRequired[bool]
    browserName: NotRequired[str]
    browserVersion: NotRequired[str]
    platformName: NotRequired[str]
    proxy: NotRequired[session_ProxyConfiguration]
    unhandledPromptBehavior: NotRequired[session_UserPromptHandler]

class session_CapabilityResponse(TypedDict):
    acceptInsecureCerts: bool
    browserName: str
    browserVersion: str
    platformName: str
    setWindowRect: bool
    userAgent: str
    proxy: NotRequired[session_ProxyConfiguration]
    unhandledPromptBehavior: NotRequired[session_UserPromptHandler]
    webSocketUrl: NotRequired[str]

type session_ProxyConfiguration = session_AutodetectProxyConfiguration | session_DirectProxyConfiguration | session_ManualProxyConfiguration | session_PacProxyConfiguration | session_SystemProxyConfiguration

class session_AutodetectProxyConfiguration(TypedDict):
    proxyType: Literal["autodetect"]

class session_DirectProxyConfiguration(TypedDict):
    proxyType: Literal["direct"]

class session_ManualProxyConfiguration(TypedDict):
    proxyType: Literal["manual"]
    httpProxy: NotRequired[str]
    sslProxy: NotRequired[str]
    noProxy: NotRequired[list[str]]
    socksProxy: NotRequired[str]
    socksVersion: NotRequired[int]

class session_SocksProxyConfiguration(TypedDict):
    socksProxy: str
    socksVersion: int

class session_PacProxyConfiguration(TypedDict):
    proxyType: Literal["pac"]
    proxyAutoconfigUrl: str

class session_SystemProxyConfiguration(TypedDict):
    proxyType: Literal["system"]

class session_UserPromptHandler(TypedDict):
    alert: NotRequired[session_UserPromptHandlerType]
    beforeUnload: NotRequired[session_UserPromptHandlerType]
    confirm: NotRequired[session_UserPromptHandlerType]
    default: NotRequired[session_UserPromptHandlerType]
    file: NotRequired[session_UserPromptHandlerType]
    prompt: NotRequired[session_UserPromptHandlerType]

type session_UserPromptHandlerType = Literal["accept", "dismiss", "ignore"]

type session_Subscription = str

class session_SubscribeParameters(TypedDict):
    events: list[str]
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

class session_UnsubscribeByIDRequest(TypedDict):
    subscriptions: list[session_Subscription]

class session_UnsubscribeByAttributesRequest(TypedDict):
    events: list[str]

class session_Status(TypedDict):
    method: Literal["session.status"]
    params: EmptyParams

class session_StatusResult(TypedDict):
    ready: bool
    message: str

class session_New(TypedDict):
    method: Literal["session.new"]
    params: session_NewParameters

class session_NewParameters(TypedDict):
    capabilities: session_CapabilitiesRequest

class session_NewResult(TypedDict):
    sessionId: str
    capabilities: session_CapabilityResponse

class session_End(TypedDict):
    method: Literal["session.end"]
    params: EmptyParams

type session_EndResult = EmptyResult

class session_Subscribe(TypedDict):
    method: Literal["session.subscribe"]
    params: session_SubscribeParameters

class session_SubscribeResult(TypedDict):
    subscription: session_Subscription

class session_Unsubscribe(TypedDict):
    method: Literal["session.unsubscribe"]
    params: session_UnsubscribeParameters

type session_UnsubscribeParameters = session_UnsubscribeByAttributesRequest | session_UnsubscribeByIDRequest

type session_UnsubscribeResult = EmptyResult

type BrowserCommand = browser_Close | browser_CreateUserContext | browser_GetClientWindows | browser_GetUserContexts | browser_RemoveUserContext | browser_SetClientWindowState | browser_SetDownloadBehavior

type BrowserResult = browser_CloseResult | browser_CreateUserContextResult | browser_GetClientWindowsResult | browser_GetUserContextsResult | browser_RemoveUserContextResult | browser_SetClientWindowStateResult | browser_SetDownloadBehaviorResult

type browser_ClientWindow = str

class browser_ClientWindowInfo(TypedDict):
    active: bool
    clientWindow: browser_ClientWindow
    height: int
    state: Literal["fullscreen", "maximized", "minimized", "normal"]
    width: int
    x: int
    y: int

type browser_UserContext = str

class browser_UserContextInfo(TypedDict):
    userContext: browser_UserContext

class browser_Close(TypedDict):
    method: Literal["browser.close"]
    params: EmptyParams

type browser_CloseResult = EmptyResult

class browser_CreateUserContext(TypedDict):
    method: Literal["browser.createUserContext"]
    params: browser_CreateUserContextParameters

class browser_CreateUserContextParameters(TypedDict):
    acceptInsecureCerts: NotRequired[bool]
    proxy: NotRequired[session_ProxyConfiguration]
    unhandledPromptBehavior: NotRequired[session_UserPromptHandler]

type browser_CreateUserContextResult = browser_UserContextInfo

class browser_GetClientWindows(TypedDict):
    method: Literal["browser.getClientWindows"]
    params: EmptyParams

class browser_GetClientWindowsResult(TypedDict):
    clientWindows: list[browser_ClientWindowInfo]

class browser_GetUserContexts(TypedDict):
    method: Literal["browser.getUserContexts"]
    params: EmptyParams

class browser_GetUserContextsResult(TypedDict):
    userContexts: list[browser_UserContextInfo]

class browser_RemoveUserContext(TypedDict):
    method: Literal["browser.removeUserContext"]
    params: browser_RemoveUserContextParameters

class browser_RemoveUserContextParameters(TypedDict):
    userContext: browser_UserContext

type browser_RemoveUserContextResult = EmptyResult

class browser_SetClientWindowState(TypedDict):
    method: Literal["browser.setClientWindowState"]
    params: browser_SetClientWindowStateParameters

class browser_SetClientWindowStateParameters(TypedDict):
    clientWindow: browser_ClientWindow
    state: NotRequired[Literal["fullscreen", "maximized", "minimized"] | Literal["normal"]]
    width: NotRequired[int]
    height: NotRequired[int]
    x: NotRequired[int]
    y: NotRequired[int]

class browser_ClientWindowNamedState(TypedDict):
    state: Literal["fullscreen", "maximized", "minimized"]

class browser_ClientWindowRectState(TypedDict):
    state: Literal["normal"]
    width: NotRequired[int]
    height: NotRequired[int]
    x: NotRequired[int]
    y: NotRequired[int]

type browser_SetClientWindowStateResult = browser_ClientWindowInfo

class browser_SetDownloadBehavior(TypedDict):
    method: Literal["browser.setDownloadBehavior"]
    params: browser_SetDownloadBehaviorParameters

class browser_SetDownloadBehaviorParameters(TypedDict):
    downloadBehavior: browser_DownloadBehavior | None
    userContexts: NotRequired[list[browser_UserContext]]

class browser_DownloadBehavior(TypedDict):
    type: NotRequired[Literal["allowed"] | Literal["denied"]]
    destinationFolder: NotRequired[str]

class browser_DownloadBehaviorAllowed(TypedDict):
    type: Literal["allowed"]
    destinationFolder: str

class browser_DownloadBehaviorDenied(TypedDict):
    type: Literal["denied"]

type browser_SetDownloadBehaviorResult = EmptyResult

type BrowsingContextCommand = browsingContext_Activate | browsingContext_CaptureScreenshot | browsingContext_Close | browsingContext_Create | browsingContext_GetTree | browsingContext_HandleUserPrompt | browsingContext_LocateNodes | browsingContext_Navigate | browsingContext_Print | browsingContext_Reload | browsingContext_SetBypassCSP | browsingContext_SetViewport | browsingContext_StartScreencast | browsingContext_StopScreencast | browsingContext_TraverseHistory

type BrowsingContextResult = browsingContext_ActivateResult | browsingContext_CaptureScreenshotResult | browsingContext_CloseResult | browsingContext_CreateResult | browsingContext_GetTreeResult | browsingContext_HandleUserPromptResult | browsingContext_LocateNodesResult | browsingContext_NavigateResult | browsingContext_PrintResult | browsingContext_ReloadResult | browsingContext_SetBypassCSPResult | browsingContext_SetViewportResult | browsingContext_StartScreencastResult | browsingContext_StopScreencastResult | browsingContext_TraverseHistoryResult

type BrowsingContextEvent = browsingContext_ContextCreated | browsingContext_ContextDestroyed | browsingContext_DomContentLoaded | browsingContext_DownloadEnd | browsingContext_DownloadWillBegin | browsingContext_FragmentNavigated | browsingContext_HistoryUpdated | browsingContext_Load | browsingContext_NavigationAborted | browsingContext_NavigationCommitted | browsingContext_NavigationFailed | browsingContext_NavigationStarted | browsingContext_UserPromptClosed | browsingContext_UserPromptOpened

type browsingContext_BrowsingContext = str

type browsingContext_InfoList = list[browsingContext_Info]

class browsingContext_BaseInfo(TypedDict):
    children: browsingContext_InfoList | None
    clientWindow: browser_ClientWindow
    context: browsingContext_BrowsingContext
    originalOpener: browsingContext_BrowsingContext | None
    url: str
    userContext: browser_UserContext
    parent: NotRequired[browsingContext_BrowsingContext | None]

class browsingContext_Info(TypedDict):
    children: NotRequired[browsingContext_InfoList | None]
    clientWindow: NotRequired[browser_ClientWindow]
    context: NotRequired[browsingContext_BrowsingContext]
    originalOpener: NotRequired[browsingContext_BrowsingContext | None]
    url: NotRequired[str]
    userContext: NotRequired[browser_UserContext]
    parent: NotRequired[browsingContext_BrowsingContext | None]

type browsingContext_Locator = browsingContext_AccessibilityLocator | browsingContext_CssLocator | browsingContext_ContextLocator | browsingContext_InnerTextLocator | browsingContext_XPathLocator

class browsingContext_AccessibilityLocator(TypedDict):
    type: Literal["accessibility"]
    value: dict[str, Any]

class browsingContext_CssLocator(TypedDict):
    type: Literal["css"]
    value: str

class browsingContext_ContextLocator(TypedDict):
    type: Literal["context"]
    value: dict[str, Any]

class browsingContext_InnerTextLocator(TypedDict):
    type: Literal["innerText"]
    value: str
    ignoreCase: NotRequired[bool]
    matchType: NotRequired[Literal["full", "partial"]]
    maxDepth: NotRequired[int]

class browsingContext_XPathLocator(TypedDict):
    type: Literal["xpath"]
    value: str

type browsingContext_Navigation = str

type browsingContext_Download = str

class browsingContext_BaseNavigationInfo(TypedDict):
    context: browsingContext_BrowsingContext
    navigation: browsingContext_Navigation | None
    timestamp: int
    url: str
    userContext: NotRequired[browser_UserContext]

class browsingContext_NavigationInfo(TypedDict):
    context: NotRequired[browsingContext_BrowsingContext]
    navigation: NotRequired[browsingContext_Navigation | None]
    timestamp: NotRequired[int]
    url: NotRequired[str]
    userContext: NotRequired[browser_UserContext]

type browsingContext_ReadinessState = Literal["none", "interactive", "complete"]

type browsingContext_UserPromptType = Literal["alert", "beforeunload", "confirm", "prompt"]

class browsingContext_Activate(TypedDict):
    method: Literal["browsingContext.activate"]
    params: browsingContext_ActivateParameters

class browsingContext_ActivateParameters(TypedDict):
    context: browsingContext_BrowsingContext

type browsingContext_ActivateResult = EmptyResult

class browsingContext_CaptureScreenshot(TypedDict):
    method: Literal["browsingContext.captureScreenshot"]
    params: browsingContext_CaptureScreenshotParameters

class browsingContext_CaptureScreenshotParameters(TypedDict):
    context: browsingContext_BrowsingContext
    origin: NotRequired[Literal["viewport", "document"]]
    format: NotRequired[browsingContext_ImageFormat]
    clip: NotRequired[browsingContext_ClipRectangle]
    imageSize: NotRequired[browsingContext_ImageSize]

class browsingContext_ImageFormat(TypedDict):
    type: str
    quality: NotRequired[int]

class browsingContext_ImageSize(TypedDict):
    maxWidth: NotRequired[int]
    maxHeight: NotRequired[int]

type browsingContext_ClipRectangle = browsingContext_BoxClipRectangle | browsingContext_ElementClipRectangle

class browsingContext_ElementClipRectangle(TypedDict):
    type: Literal["element"]
    element: script_SharedReference

class browsingContext_BoxClipRectangle(TypedDict):
    type: Literal["box"]
    x: float
    y: float
    width: float
    height: float

class browsingContext_CaptureScreenshotResult(TypedDict):
    data: str

class browsingContext_Close(TypedDict):
    method: Literal["browsingContext.close"]
    params: browsingContext_CloseParameters

class browsingContext_CloseParameters(TypedDict):
    context: browsingContext_BrowsingContext
    promptUnload: NotRequired[bool]

type browsingContext_CloseResult = EmptyResult

class browsingContext_Create(TypedDict):
    method: Literal["browsingContext.create"]
    params: browsingContext_CreateParameters

type browsingContext_CreateType = Literal["tab", "window"]

class browsingContext_CreateParameters(TypedDict):
    type: browsingContext_CreateType
    referenceContext: NotRequired[browsingContext_BrowsingContext]
    background: NotRequired[bool]
    userContext: NotRequired[browser_UserContext]

class browsingContext_CreateResult(TypedDict):
    context: browsingContext_BrowsingContext
    userContext: NotRequired[browser_UserContext]

class browsingContext_GetTree(TypedDict):
    method: Literal["browsingContext.getTree"]
    params: browsingContext_GetTreeParameters

class browsingContext_GetTreeParameters(TypedDict):
    maxDepth: NotRequired[int]
    root: NotRequired[browsingContext_BrowsingContext]

class browsingContext_GetTreeResult(TypedDict):
    contexts: browsingContext_InfoList

class browsingContext_HandleUserPrompt(TypedDict):
    method: Literal["browsingContext.handleUserPrompt"]
    params: browsingContext_HandleUserPromptParameters

class browsingContext_HandleUserPromptParameters(TypedDict):
    context: browsingContext_BrowsingContext
    accept: NotRequired[bool]
    userText: NotRequired[str]

type browsingContext_HandleUserPromptResult = EmptyResult

class browsingContext_LocateNodes(TypedDict):
    method: Literal["browsingContext.locateNodes"]
    params: browsingContext_LocateNodesParameters

class browsingContext_LocateNodesParameters(TypedDict):
    context: browsingContext_BrowsingContext
    locator: browsingContext_Locator
    maxNodeCount: NotRequired[int]
    serializationOptions: NotRequired[script_SerializationOptions]
    startNodes: NotRequired[list[script_SharedReference]]

class browsingContext_LocateNodesResult(TypedDict):
    nodes: list[script_NodeRemoteValue]

class browsingContext_Navigate(TypedDict):
    method: Literal["browsingContext.navigate"]
    params: browsingContext_NavigateParameters

class browsingContext_NavigateParameters(TypedDict):
    context: browsingContext_BrowsingContext
    url: str
    wait: NotRequired[browsingContext_ReadinessState]

class browsingContext_NavigateResult(TypedDict):
    navigation: browsingContext_Navigation | None
    url: str

class browsingContext_Print(TypedDict):
    method: Literal["browsingContext.print"]
    params: browsingContext_PrintParameters

class browsingContext_PrintParameters(TypedDict):
    context: browsingContext_BrowsingContext
    background: NotRequired[bool]
    margin: NotRequired[browsingContext_PrintMarginParameters]
    orientation: NotRequired[Literal["portrait", "landscape"]]
    page: NotRequired[browsingContext_PrintPageParameters]
    pageRanges: NotRequired[list[int | str]]
    scale: NotRequired[int]
    shrinkToFit: NotRequired[bool]

class browsingContext_PrintMarginParameters(TypedDict):
    bottom: NotRequired[float]
    left: NotRequired[float]
    right: NotRequired[float]
    top: NotRequired[float]

class browsingContext_PrintPageParameters(TypedDict):
    height: NotRequired[float]
    width: NotRequired[float]

class browsingContext_PrintResult(TypedDict):
    data: str

class browsingContext_Reload(TypedDict):
    method: Literal["browsingContext.reload"]
    params: browsingContext_ReloadParameters

class browsingContext_ReloadParameters(TypedDict):
    context: browsingContext_BrowsingContext
    ignoreCache: NotRequired[bool]
    wait: NotRequired[browsingContext_ReadinessState]

type browsingContext_ReloadResult = browsingContext_NavigateResult

class browsingContext_SetBypassCSP(TypedDict):
    method: Literal["browsingContext.setBypassCSP"]
    params: browsingContext_SetBypassCSPParameters

class browsingContext_SetBypassCSPParameters(TypedDict):
    bypass: bool | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type browsingContext_SetBypassCSPResult = EmptyResult

class browsingContext_SetViewport(TypedDict):
    method: Literal["browsingContext.setViewport"]
    params: browsingContext_SetViewportParameters

class browsingContext_SetViewportParameters(TypedDict):
    context: NotRequired[browsingContext_BrowsingContext]
    viewport: NotRequired[browsingContext_Viewport | None]
    devicePixelRatio: NotRequired[float | None]
    userContexts: NotRequired[list[browser_UserContext]]

class browsingContext_Viewport(TypedDict):
    width: int
    height: int

type browsingContext_SetViewportResult = EmptyResult

class browsingContext_StartScreencast(TypedDict):
    method: Literal["browsingContext.startScreencast"]
    params: browsingContext_StartScreencastParameters

class browsingContext_StartScreencastParameters(TypedDict):
    context: browsingContext_BrowsingContext
    destinationFolder: NotRequired[str]
    mimeType: NotRequired[str]
    video: NotRequired[browsingContext_MediaTrackConstraints]
    audio: NotRequired[bool]

class browsingContext_MediaTrackConstraints(TypedDict):
    width: NotRequired[int]
    height: NotRequired[int]
    frameRate: NotRequired[int]

class browsingContext_StartScreencastResult(TypedDict):
    screencast: browsingContext_Screencast
    path: str

type browsingContext_Screencast = str

class browsingContext_StopScreencast(TypedDict):
    method: Literal["browsingContext.stopScreencast"]
    params: browsingContext_StopScreencastParameters

class browsingContext_StopScreencastParameters(TypedDict):
    screencast: browsingContext_Screencast

class browsingContext_StopScreencastResult(TypedDict):
    path: str
    error: NotRequired[str]

class browsingContext_TraverseHistory(TypedDict):
    method: Literal["browsingContext.traverseHistory"]
    params: browsingContext_TraverseHistoryParameters

class browsingContext_TraverseHistoryParameters(TypedDict):
    context: browsingContext_BrowsingContext
    delta: int

type browsingContext_TraverseHistoryResult = EmptyResult

class browsingContext_ContextCreated(TypedDict):
    method: Literal["browsingContext.contextCreated"]
    params: browsingContext_ContextCreatedParameters

class browsingContext_ContextCreatedParameters(TypedDict):
    hasPlannedNavigation: bool
    children: NotRequired[browsingContext_InfoList | None]
    clientWindow: NotRequired[browser_ClientWindow]
    context: NotRequired[browsingContext_BrowsingContext]
    originalOpener: NotRequired[browsingContext_BrowsingContext | None]
    url: NotRequired[str]
    userContext: NotRequired[browser_UserContext]
    parent: NotRequired[browsingContext_BrowsingContext | None]

class browsingContext_ContextDestroyed(TypedDict):
    method: Literal["browsingContext.contextDestroyed"]
    params: browsingContext_Info

class browsingContext_NavigationStarted(TypedDict):
    method: Literal["browsingContext.navigationStarted"]
    params: browsingContext_NavigationInfo

class browsingContext_FragmentNavigated(TypedDict):
    method: Literal["browsingContext.fragmentNavigated"]
    params: browsingContext_NavigationInfo

class browsingContext_HistoryUpdated(TypedDict):
    method: Literal["browsingContext.historyUpdated"]
    params: browsingContext_HistoryUpdatedParameters

class browsingContext_HistoryUpdatedParameters(TypedDict):
    context: browsingContext_BrowsingContext
    timestamp: int
    url: str
    userContext: NotRequired[browser_UserContext]

class browsingContext_DomContentLoaded(TypedDict):
    method: Literal["browsingContext.domContentLoaded"]
    params: browsingContext_NavigationInfo

class browsingContext_Load(TypedDict):
    method: Literal["browsingContext.load"]
    params: browsingContext_NavigationInfo

class browsingContext_DownloadWillBegin(TypedDict):
    method: Literal["browsingContext.downloadWillBegin"]
    params: browsingContext_DownloadWillBeginParams

class browsingContext_DownloadWillBeginParams(TypedDict):
    download: browsingContext_Download
    suggestedFilename: str
    context: NotRequired[browsingContext_BrowsingContext]
    navigation: NotRequired[browsingContext_Navigation | None]
    timestamp: NotRequired[int]
    url: NotRequired[str]
    userContext: NotRequired[browser_UserContext]

class browsingContext_DownloadEnd(TypedDict):
    method: Literal["browsingContext.downloadEnd"]
    params: browsingContext_DownloadEndParams

class browsingContext_DownloadEndParams(TypedDict):
    status: NotRequired[Literal["canceled"] | Literal["complete"]]
    download: NotRequired[browsingContext_Download]
    context: NotRequired[browsingContext_BrowsingContext]
    navigation: NotRequired[browsingContext_Navigation | None]
    timestamp: NotRequired[int]
    url: NotRequired[str]
    userContext: NotRequired[browser_UserContext]
    filepath: NotRequired[str | None]

class browsingContext_DownloadCanceledParams(TypedDict):
    status: Literal["canceled"]
    download: browsingContext_Download
    context: NotRequired[browsingContext_BrowsingContext]
    navigation: NotRequired[browsingContext_Navigation | None]
    timestamp: NotRequired[int]
    url: NotRequired[str]
    userContext: NotRequired[browser_UserContext]

class browsingContext_DownloadCompleteParams(TypedDict):
    status: Literal["complete"]
    download: browsingContext_Download
    filepath: str | None
    context: NotRequired[browsingContext_BrowsingContext]
    navigation: NotRequired[browsingContext_Navigation | None]
    timestamp: NotRequired[int]
    url: NotRequired[str]
    userContext: NotRequired[browser_UserContext]

class browsingContext_NavigationAborted(TypedDict):
    method: Literal["browsingContext.navigationAborted"]
    params: browsingContext_NavigationInfo

class browsingContext_NavigationCommitted(TypedDict):
    method: Literal["browsingContext.navigationCommitted"]
    params: browsingContext_NavigationInfo

class browsingContext_NavigationFailed(TypedDict):
    method: Literal["browsingContext.navigationFailed"]
    params: browsingContext_NavigationInfo

class browsingContext_UserPromptClosed(TypedDict):
    method: Literal["browsingContext.userPromptClosed"]
    params: browsingContext_UserPromptClosedParameters

class browsingContext_UserPromptClosedParameters(TypedDict):
    context: browsingContext_BrowsingContext
    accepted: bool
    type: browsingContext_UserPromptType
    userContext: NotRequired[browser_UserContext]
    userText: NotRequired[str]

class browsingContext_UserPromptOpened(TypedDict):
    method: Literal["browsingContext.userPromptOpened"]
    params: browsingContext_UserPromptOpenedParameters

class browsingContext_UserPromptOpenedParameters(TypedDict):
    context: browsingContext_BrowsingContext
    handler: session_UserPromptHandlerType
    message: str
    type: browsingContext_UserPromptType
    userContext: NotRequired[browser_UserContext]
    defaultValue: NotRequired[str]

type EmulationCommand = emulation_SetForcedColorsModeThemeOverride | emulation_SetGeolocationOverride | emulation_SetLocaleOverride | emulation_SetMediaFeaturesOverride | emulation_SetNetworkConditions | emulation_SetScreenOrientationOverride | emulation_SetScreenSettingsOverride | emulation_SetScriptingEnabled | emulation_SetScrollbarTypeOverride | emulation_SetTextLayoutModeOverride | emulation_SetTimezoneOverride | emulation_SetTouchOverride | emulation_SetUserAgentOverride | emulation_SetViewportMetaOverride

type EmulationResult = emulation_SetForcedColorsModeThemeOverrideResult | emulation_SetGeolocationOverrideResult | emulation_SetLocaleOverrideResult | emulation_SetMediaFeaturesOverrideResult | emulation_SetScreenOrientationOverrideResult | emulation_SetScriptingEnabledResult | emulation_SetScrollbarTypeOverrideResult | emulation_SetTextLayoutModeOverrideResult | emulation_SetTimezoneOverrideResult | emulation_SetTouchOverrideResult | emulation_SetUserAgentOverrideResult | emulation_SetViewportMetaOverrideResult

class emulation_SetForcedColorsModeThemeOverride(TypedDict):
    method: Literal["emulation.setForcedColorsModeThemeOverride"]
    params: emulation_SetForcedColorsModeThemeOverrideParameters

class emulation_SetForcedColorsModeThemeOverrideParameters(TypedDict):
    theme: emulation_ForcedColorsModeTheme | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_ForcedColorsModeTheme = Literal["light", "dark"]

type emulation_SetForcedColorsModeThemeOverrideResult = EmptyResult

class emulation_SetGeolocationOverride(TypedDict):
    method: Literal["emulation.setGeolocationOverride"]
    params: emulation_SetGeolocationOverrideParameters

class emulation_SetGeolocationOverrideParameters(TypedDict):
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]
    coordinates: NotRequired[emulation_GeolocationCoordinates | None]
    error: NotRequired[emulation_GeolocationPositionError]

class emulation_GeolocationCoordinates(TypedDict):
    latitude: int
    longitude: int
    accuracy: NotRequired[float]
    altitude: NotRequired[float | None]
    altitudeAccuracy: NotRequired[float | None]
    heading: NotRequired[int | None]
    speed: NotRequired[float | None]

class emulation_GeolocationPositionError(TypedDict):
    type: Literal["positionUnavailable"]

type emulation_SetGeolocationOverrideResult = EmptyResult

class emulation_SetLocaleOverride(TypedDict):
    method: Literal["emulation.setLocaleOverride"]
    params: emulation_SetLocaleOverrideParameters

class emulation_SetLocaleOverrideParameters(TypedDict):
    locale: str | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetLocaleOverrideResult = EmptyResult

class emulation_SetMediaFeaturesOverride(TypedDict):
    method: Literal["emulation.setMediaFeaturesOverride"]
    params: emulation_SetMediaFeaturesOverrideParameters

class emulation_SetMediaFeaturesOverrideParameters(TypedDict):
    features: emulation_MediaFeatures | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

emulation_MediaFeatures = TypedDict("emulation_MediaFeatures", {"any-hover": "NotRequired[Literal[\"none\"] | Literal[\"hover\"] | None]", "any-pointer": "NotRequired[Literal[\"none\"] | Literal[\"coarse\"] | Literal[\"fine\"] | None]", "color": "NotRequired[int | None]", "color-gamut": "NotRequired[Literal[\"srgb\"] | Literal[\"p3\"] | Literal[\"rec2020\"] | None]", "color-index": "NotRequired[int | None]", "display-mode": "NotRequired[Literal[\"fullscreen\"] | Literal[\"standalone\"] | Literal[\"minimal-ui\"] | Literal[\"browser\"] | Literal[\"picture-in-picture\"] | None]", "dynamic-range": "NotRequired[Literal[\"standard\"] | Literal[\"high\"] | None]", "environment-blending": "NotRequired[Literal[\"opaque\"] | Literal[\"additive\"] | Literal[\"subtractive\"] | None]", "forced-colors": "NotRequired[Literal[\"none\"] | Literal[\"active\"] | None]", "grid": "NotRequired[int | int | None]", "horizontal-viewport-segments": "NotRequired[int | None]", "hover": "NotRequired[Literal[\"none\"] | Literal[\"hover\"] | None]", "inverted-colors": "NotRequired[Literal[\"none\"] | Literal[\"inverted\"] | None]", "monochrome": "NotRequired[int | None]", "nav-controls": "NotRequired[Literal[\"none\"] | Literal[\"back\"] | None]", "overflow-block": "NotRequired[Literal[\"none\"] | Literal[\"scroll\"] | Literal[\"optional-paged\"] | Literal[\"paged\"] | None]", "overflow-inline": "NotRequired[Literal[\"none\"] | Literal[\"scroll\"] | None]", "pointer": "NotRequired[Literal[\"none\"] | Literal[\"coarse\"] | Literal[\"fine\"] | None]", "prefers-color-scheme": "NotRequired[Literal[\"light\"] | Literal[\"dark\"] | None]", "prefers-contrast": "NotRequired[Literal[\"no-preference\"] | Literal[\"more\"] | Literal[\"less\"] | Literal[\"custom\"] | None]", "prefers-reduced-data": "NotRequired[Literal[\"no-preference\"] | Literal[\"reduce\"] | None]", "prefers-reduced-motion": "NotRequired[Literal[\"no-preference\"] | Literal[\"reduce\"] | None]", "prefers-reduced-transparency": "NotRequired[Literal[\"no-preference\"] | Literal[\"reduce\"] | None]", "scan": "NotRequired[Literal[\"interlace\"] | Literal[\"progressive\"] | None]", "scripting": "NotRequired[Literal[\"none\"] | Literal[\"initial-only\"] | Literal[\"enabled\"] | None]", "update": "NotRequired[Literal[\"none\"] | Literal[\"slow\"] | Literal[\"fast\"] | None]", "vertical-viewport-segments": "NotRequired[int | None]", "video-color-gamut": "NotRequired[Literal[\"srgb\"] | Literal[\"p3\"] | Literal[\"rec2020\"] | None]", "video-dynamic-range": "NotRequired[Literal[\"standard\"] | Literal[\"high\"] | None]"})

type emulation_SetMediaFeaturesOverrideResult = EmptyResult

class emulation_SetNetworkConditions(TypedDict):
    method: Literal["emulation.setNetworkConditions"]
    params: emulation_SetNetworkConditionsParameters

class emulation_SetNetworkConditionsParameters(TypedDict):
    networkConditions: emulation_NetworkConditions | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_NetworkConditions = emulation_NetworkConditionsOffline

class emulation_NetworkConditionsOffline(TypedDict):
    type: Literal["offline"]

type emulation_SetNetworkConditionsResult = EmptyResult

class emulation_SetScreenSettingsOverride(TypedDict):
    method: Literal["emulation.setScreenSettingsOverride"]
    params: emulation_SetScreenSettingsOverrideParameters

class emulation_ScreenArea(TypedDict):
    width: int
    height: int

class emulation_SetScreenSettingsOverrideParameters(TypedDict):
    screenArea: emulation_ScreenArea | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetScreenSettingsOverrideResult = EmptyResult

class emulation_SetScreenOrientationOverride(TypedDict):
    method: Literal["emulation.setScreenOrientationOverride"]
    params: emulation_SetScreenOrientationOverrideParameters

type emulation_ScreenOrientationNatural = Literal["portrait", "landscape"]

type emulation_ScreenOrientationType = Literal["portrait-primary", "portrait-secondary", "landscape-primary", "landscape-secondary"]

class emulation_ScreenOrientation(TypedDict):
    natural: emulation_ScreenOrientationNatural
    type: emulation_ScreenOrientationType

class emulation_SetScreenOrientationOverrideParameters(TypedDict):
    screenOrientation: emulation_ScreenOrientation | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetScreenOrientationOverrideResult = EmptyResult

class emulation_SetUserAgentOverride(TypedDict):
    method: Literal["emulation.setUserAgentOverride"]
    params: emulation_SetUserAgentOverrideParameters

class emulation_SetUserAgentOverrideParameters(TypedDict):
    userAgent: str | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetUserAgentOverrideResult = EmptyResult

class emulation_SetViewportMetaOverride(TypedDict):
    method: Literal["emulation.setViewportMetaOverride"]
    params: emulation_SetViewportMetaOverrideParameters

class emulation_SetViewportMetaOverrideParameters(TypedDict):
    viewportMeta: bool | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetViewportMetaOverrideResult = EmptyResult

class emulation_SetScriptingEnabled(TypedDict):
    method: Literal["emulation.setScriptingEnabled"]
    params: emulation_SetScriptingEnabledParameters

class emulation_SetScriptingEnabledParameters(TypedDict):
    enabled: bool | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetScriptingEnabledResult = EmptyResult

class emulation_SetScrollbarTypeOverride(TypedDict):
    method: Literal["emulation.setScrollbarTypeOverride"]
    params: emulation_SetScrollbarTypeOverrideParameters

class emulation_SetScrollbarTypeOverrideParameters(TypedDict):
    scrollbarType: Literal["classic"] | Literal["overlay"] | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetScrollbarTypeOverrideResult = EmptyResult

class emulation_SetTextLayoutModeOverride(TypedDict):
    method: Literal["emulation.setTextLayoutModeOverride"]
    params: emulation_SetTextLayoutModeOverrideParameters

class emulation_SetTextLayoutModeOverrideParameters(TypedDict):
    textLayoutMode: emulation_TextLayoutMode | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_TextLayoutMode = Literal["mobile"]

type emulation_SetTextLayoutModeOverrideResult = EmptyResult

class emulation_SetTimezoneOverride(TypedDict):
    method: Literal["emulation.setTimezoneOverride"]
    params: emulation_SetTimezoneOverrideParameters

class emulation_SetTimezoneOverrideParameters(TypedDict):
    timezone: str | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetTimezoneOverrideResult = EmptyResult

class emulation_SetTouchOverride(TypedDict):
    method: Literal["emulation.setTouchOverride"]
    params: emulation_SetTouchOverrideParameters

class emulation_SetTouchOverrideParameters(TypedDict):
    maxTouchPoints: int | None
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type emulation_SetTouchOverrideResult = EmptyResult

type NetworkCommand = network_AddDataCollector | network_AddIntercept | network_ContinueRequest | network_ContinueResponse | network_ContinueWithAuth | network_DisownData | network_FailRequest | network_GetData | network_ProvideResponse | network_RemoveDataCollector | network_RemoveIntercept | network_SetCacheBehavior | network_SetExtraHeaders

type NetworkResult = network_AddDataCollectorResult | network_AddInterceptResult | network_ContinueRequestResult | network_ContinueResponseResult | network_ContinueWithAuthResult | network_DisownDataResult | network_FailRequestResult | network_GetDataResult | network_ProvideResponseResult | network_RemoveDataCollectorResult | network_RemoveInterceptResult | network_SetCacheBehaviorResult | network_SetExtraHeadersResult

type NetworkEvent = network_AuthRequired | network_BeforeRequestSent | network_FetchError | network_ResponseCompleted | network_ResponseStarted

class network_AuthChallenge(TypedDict):
    scheme: str
    realm: str

class network_AuthCredentials(TypedDict):
    type: Literal["password"]
    username: str
    password: str

class network_BaseParameters(TypedDict):
    context: browsingContext_BrowsingContext | None
    isBlocked: bool
    navigation: browsingContext_Navigation | None
    redirectCount: int
    request: network_RequestData
    timestamp: int
    userContext: NotRequired[browser_UserContext | None]
    intercepts: NotRequired[list[network_Intercept]]

type network_BytesValue = network_StringValue | network_Base64Value

class network_StringValue(TypedDict):
    type: Literal["string"]
    value: str

class network_Base64Value(TypedDict):
    type: Literal["base64"]
    value: str

type network_Collector = str

type network_CollectorType = Literal["blob"]

type network_SameSite = Literal["strict", "lax", "none", "default"]

class network_Cookie(TypedDict):
    name: str
    value: network_BytesValue
    domain: str
    path: str
    size: int
    httpOnly: bool
    secure: bool
    sameSite: network_SameSite
    expiry: NotRequired[int]

class network_CookieHeader(TypedDict):
    name: str
    value: network_BytesValue

type network_DataType = Literal["request", "response"]

class network_FetchTimingInfo(TypedDict):
    timeOrigin: float
    requestTime: float
    redirectStart: float
    redirectEnd: float
    fetchStart: float
    dnsStart: float
    dnsEnd: float
    connectStart: float
    connectEnd: float
    tlsStart: float
    requestStart: float
    responseStart: float
    responseEnd: float

class network_Header(TypedDict):
    name: str
    value: network_BytesValue

class network_Initiator(TypedDict):
    columnNumber: NotRequired[int]
    lineNumber: NotRequired[int]
    request: NotRequired[network_Request]
    stackTrace: NotRequired[script_StackTrace]
    type: NotRequired[Literal["parser", "script", "preflight", "other"]]

type network_Intercept = str

type network_Request = str

class network_RequestData(TypedDict):
    request: network_Request
    url: str
    method: str
    headers: list[network_Header]
    cookies: list[network_Cookie]
    headersSize: int
    bodySize: int | None
    destination: str
    initiatorType: str | None
    timings: network_FetchTimingInfo

class network_ResponseContent(TypedDict):
    size: int

class network_ResponseData(TypedDict):
    url: str
    protocol: str
    status: int
    statusText: str
    fromCache: bool
    headers: list[network_Header]
    mimeType: str
    bytesReceived: int
    headersSize: int | None
    bodySize: int | None
    content: network_ResponseContent
    authChallenges: NotRequired[list[network_AuthChallenge]]

class network_SetCookieHeader(TypedDict):
    name: str
    value: network_BytesValue
    domain: NotRequired[str]
    httpOnly: NotRequired[bool]
    expiry: NotRequired[str]
    maxAge: NotRequired[int]
    path: NotRequired[str]
    sameSite: NotRequired[network_SameSite]
    secure: NotRequired[bool]

type network_UrlPattern = network_UrlPatternPattern | network_UrlPatternString

class network_UrlPatternPattern(TypedDict):
    type: Literal["pattern"]
    protocol: NotRequired[str]
    hostname: NotRequired[str]
    port: NotRequired[str]
    pathname: NotRequired[str]
    search: NotRequired[str]

class network_UrlPatternString(TypedDict):
    type: Literal["string"]
    pattern: str

class network_AddDataCollector(TypedDict):
    method: Literal["network.addDataCollector"]
    params: network_AddDataCollectorParameters

class network_AddDataCollectorParameters(TypedDict):
    dataTypes: list[network_DataType]
    maxEncodedDataSize: int
    collectorType: NotRequired[network_CollectorType]
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

class network_AddDataCollectorResult(TypedDict):
    collector: network_Collector

class network_AddIntercept(TypedDict):
    method: Literal["network.addIntercept"]
    params: network_AddInterceptParameters

class network_AddInterceptParameters(TypedDict):
    phases: list[network_InterceptPhase]
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    urlPatterns: NotRequired[list[network_UrlPattern]]

type network_InterceptPhase = Literal["beforeRequestSent", "responseStarted", "authRequired"]

class network_AddInterceptResult(TypedDict):
    intercept: network_Intercept

class network_ContinueRequest(TypedDict):
    method: Literal["network.continueRequest"]
    params: network_ContinueRequestParameters

class network_ContinueRequestParameters(TypedDict):
    request: network_Request
    body: NotRequired[network_BytesValue]
    cookies: NotRequired[list[network_CookieHeader]]
    headers: NotRequired[list[network_Header]]
    method: NotRequired[str]
    url: NotRequired[str]

type network_ContinueRequestResult = EmptyResult

class network_ContinueResponse(TypedDict):
    method: Literal["network.continueResponse"]
    params: network_ContinueResponseParameters

class network_ContinueResponseParameters(TypedDict):
    request: network_Request
    cookies: NotRequired[list[network_SetCookieHeader]]
    credentials: NotRequired[network_AuthCredentials]
    headers: NotRequired[list[network_Header]]
    reasonPhrase: NotRequired[str]
    statusCode: NotRequired[int]

type network_ContinueResponseResult = EmptyResult

class network_ContinueWithAuth(TypedDict):
    method: Literal["network.continueWithAuth"]
    params: network_ContinueWithAuthParameters

class network_ContinueWithAuthParameters(TypedDict):
    request: network_Request
    action: NotRequired[Literal["provideCredentials"] | Literal["default", "cancel"]]
    credentials: NotRequired[network_AuthCredentials]

class network_ContinueWithAuthCredentials(TypedDict):
    action: Literal["provideCredentials"]
    credentials: network_AuthCredentials

class network_ContinueWithAuthNoCredentials(TypedDict):
    action: Literal["default", "cancel"]

type network_ContinueWithAuthResult = EmptyResult

class network_DisownData(TypedDict):
    method: Literal["network.disownData"]
    params: network_DisownDataParameters

class network_DisownDataParameters(TypedDict):
    dataType: network_DataType
    collector: network_Collector
    request: network_Request

type network_DisownDataResult = EmptyResult

class network_FailRequest(TypedDict):
    method: Literal["network.failRequest"]
    params: network_FailRequestParameters

class network_FailRequestParameters(TypedDict):
    request: network_Request

type network_FailRequestResult = EmptyResult

class network_GetData(TypedDict):
    method: Literal["network.getData"]
    params: network_GetDataParameters

class network_GetDataParameters(TypedDict):
    dataType: network_DataType
    collector: NotRequired[network_Collector]
    disown: NotRequired[bool]
    request: network_Request

class network_GetDataResult(TypedDict):
    bytes: network_BytesValue

class network_ProvideResponse(TypedDict):
    method: Literal["network.provideResponse"]
    params: network_ProvideResponseParameters

class network_ProvideResponseParameters(TypedDict):
    request: network_Request
    body: NotRequired[network_BytesValue]
    cookies: NotRequired[list[network_SetCookieHeader]]
    headers: NotRequired[list[network_Header]]
    reasonPhrase: NotRequired[str]
    statusCode: NotRequired[int]

type network_ProvideResponseResult = EmptyResult

class network_RemoveDataCollector(TypedDict):
    method: Literal["network.removeDataCollector"]
    params: network_RemoveDataCollectorParameters

class network_RemoveDataCollectorParameters(TypedDict):
    collector: network_Collector

type network_RemoveDataCollectorResult = EmptyResult

class network_RemoveIntercept(TypedDict):
    method: Literal["network.removeIntercept"]
    params: network_RemoveInterceptParameters

class network_RemoveInterceptParameters(TypedDict):
    intercept: network_Intercept

type network_RemoveInterceptResult = EmptyResult

class network_SetCacheBehavior(TypedDict):
    method: Literal["network.setCacheBehavior"]
    params: network_SetCacheBehaviorParameters

class network_SetCacheBehaviorParameters(TypedDict):
    cacheBehavior: Literal["default", "bypass"]
    contexts: NotRequired[list[browsingContext_BrowsingContext]]

type network_SetCacheBehaviorResult = EmptyResult

class network_SetExtraHeaders(TypedDict):
    method: Literal["network.setExtraHeaders"]
    params: network_SetExtraHeadersParameters

class network_SetExtraHeadersParameters(TypedDict):
    headers: list[network_Header]
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]

type network_SetExtraHeadersResult = EmptyResult

class network_AuthRequired(TypedDict):
    method: Literal["network.authRequired"]
    params: network_AuthRequiredParameters

class network_AuthRequiredParameters(TypedDict):
    response: network_ResponseData
    context: NotRequired[browsingContext_BrowsingContext | None]
    isBlocked: NotRequired[bool]
    navigation: NotRequired[browsingContext_Navigation | None]
    redirectCount: NotRequired[int]
    request: NotRequired[network_RequestData]
    timestamp: NotRequired[int]
    userContext: NotRequired[browser_UserContext | None]
    intercepts: NotRequired[list[network_Intercept]]

class network_BeforeRequestSent(TypedDict):
    method: Literal["network.beforeRequestSent"]
    params: network_BeforeRequestSentParameters

class network_BeforeRequestSentParameters(TypedDict):
    initiator: NotRequired[network_Initiator]
    context: NotRequired[browsingContext_BrowsingContext | None]
    isBlocked: NotRequired[bool]
    navigation: NotRequired[browsingContext_Navigation | None]
    redirectCount: NotRequired[int]
    request: NotRequired[network_RequestData]
    timestamp: NotRequired[int]
    userContext: NotRequired[browser_UserContext | None]
    intercepts: NotRequired[list[network_Intercept]]

class network_FetchError(TypedDict):
    method: Literal["network.fetchError"]
    params: network_FetchErrorParameters

class network_FetchErrorParameters(TypedDict):
    errorText: str
    context: NotRequired[browsingContext_BrowsingContext | None]
    isBlocked: NotRequired[bool]
    navigation: NotRequired[browsingContext_Navigation | None]
    redirectCount: NotRequired[int]
    request: NotRequired[network_RequestData]
    timestamp: NotRequired[int]
    userContext: NotRequired[browser_UserContext | None]
    intercepts: NotRequired[list[network_Intercept]]

class network_ResponseCompleted(TypedDict):
    method: Literal["network.responseCompleted"]
    params: network_ResponseCompletedParameters

class network_ResponseCompletedParameters(TypedDict):
    response: network_ResponseData
    context: NotRequired[browsingContext_BrowsingContext | None]
    isBlocked: NotRequired[bool]
    navigation: NotRequired[browsingContext_Navigation | None]
    redirectCount: NotRequired[int]
    request: NotRequired[network_RequestData]
    timestamp: NotRequired[int]
    userContext: NotRequired[browser_UserContext | None]
    intercepts: NotRequired[list[network_Intercept]]

class network_ResponseStarted(TypedDict):
    method: Literal["network.responseStarted"]
    params: network_ResponseStartedParameters

class network_ResponseStartedParameters(TypedDict):
    response: network_ResponseData
    context: NotRequired[browsingContext_BrowsingContext | None]
    isBlocked: NotRequired[bool]
    navigation: NotRequired[browsingContext_Navigation | None]
    redirectCount: NotRequired[int]
    request: NotRequired[network_RequestData]
    timestamp: NotRequired[int]
    userContext: NotRequired[browser_UserContext | None]
    intercepts: NotRequired[list[network_Intercept]]

type ScriptCommand = script_AddPreloadScript | script_CallFunction | script_Disown | script_Evaluate | script_GetRealms | script_RemovePreloadScript

type ScriptResult = script_AddPreloadScriptResult | script_CallFunctionResult | script_DisownResult | script_EvaluateResult | script_GetRealmsResult | script_RemovePreloadScriptResult

type ScriptEvent = script_Message | script_RealmCreated | script_RealmDestroyed

type script_Channel = str

class script_ChannelValue(TypedDict):
    type: Literal["channel"]
    value: script_ChannelProperties

class script_ChannelProperties(TypedDict):
    channel: script_Channel
    serializationOptions: NotRequired[script_SerializationOptions]
    ownership: NotRequired[script_ResultOwnership]

type script_EvaluationResult = script_EvaluationResultSuccess | script_EvaluationResultException

class script_EvaluationResultSuccess(TypedDict):
    type: Literal["success"]
    result: script_RemoteValue
    realm: script_Realm

class script_EvaluationResultException(TypedDict):
    type: Literal["exception"]
    exceptionDetails: script_ExceptionDetails
    realm: script_Realm

class script_ExceptionDetails(TypedDict):
    columnNumber: int
    exception: script_RemoteValue
    lineNumber: int
    stackTrace: script_StackTrace
    text: str

type script_Handle = str

type script_InternalId = str

type script_LocalValue = script_RemoteReference | script_PrimitiveProtocolValue | script_ChannelValue | script_ArrayLocalValue | dict[str, Any] | script_MapLocalValue | script_ObjectLocalValue | dict[str, Any] | script_SetLocalValue

type script_ListLocalValue = list[script_LocalValue]

class script_ArrayLocalValue(TypedDict):
    type: Literal["array"]
    value: script_ListLocalValue

class script_DateLocalValue(TypedDict):
    type: Literal["date"]
    value: str

type script_MappingLocalValue = list[tuple[script_LocalValue | str, script_LocalValue]]

class script_MapLocalValue(TypedDict):
    type: Literal["map"]
    value: script_MappingLocalValue

class script_ObjectLocalValue(TypedDict):
    type: Literal["object"]
    value: script_MappingLocalValue

class script_RegExpValue(TypedDict):
    pattern: str
    flags: NotRequired[str]

class script_RegExpLocalValue(TypedDict):
    type: Literal["regexp"]
    value: script_RegExpValue

class script_SetLocalValue(TypedDict):
    type: Literal["set"]
    value: script_ListLocalValue

type script_PreloadScript = str

type script_Realm = str

type script_PrimitiveProtocolValue = script_UndefinedValue | script_NullValue | script_StringValue | script_NumberValue | script_BooleanValue | script_BigIntValue

class script_UndefinedValue(TypedDict):
    type: Literal["undefined"]

class script_NullValue(TypedDict):
    type: Literal["null"]

class script_StringValue(TypedDict):
    type: Literal["string"]
    value: str

type script_SpecialNumber = Literal["NaN", "-0", "Infinity", "-Infinity"]

class script_NumberValue(TypedDict):
    type: Literal["number"]
    value: float | script_SpecialNumber

class script_BooleanValue(TypedDict):
    type: Literal["boolean"]
    value: bool

class script_BigIntValue(TypedDict):
    type: Literal["bigint"]
    value: str

type script_RealmInfo = script_WindowRealmInfo | script_DedicatedWorkerRealmInfo | script_SharedWorkerRealmInfo | script_ServiceWorkerRealmInfo | script_WorkerRealmInfo | script_PaintWorkletRealmInfo | script_AudioWorkletRealmInfo | script_WorkletRealmInfo

class script_BaseRealmInfo(TypedDict):
    realm: script_Realm
    origin: str

class script_WindowRealmInfo(TypedDict):
    type: Literal["window"]
    context: browsingContext_BrowsingContext
    userContext: NotRequired[browser_UserContext]
    sandbox: NotRequired[str]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

class script_DedicatedWorkerRealmInfo(TypedDict):
    type: Literal["dedicated-worker"]
    owners: list[script_Realm]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

class script_SharedWorkerRealmInfo(TypedDict):
    type: Literal["shared-worker"]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

class script_ServiceWorkerRealmInfo(TypedDict):
    type: Literal["service-worker"]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

class script_WorkerRealmInfo(TypedDict):
    type: Literal["worker"]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

class script_PaintWorkletRealmInfo(TypedDict):
    type: Literal["paint-worklet"]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

class script_AudioWorkletRealmInfo(TypedDict):
    type: Literal["audio-worklet"]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

class script_WorkletRealmInfo(TypedDict):
    type: Literal["worklet"]
    realm: NotRequired[script_Realm]
    origin: NotRequired[str]

type script_RealmType = Literal["window", "dedicated-worker", "shared-worker", "service-worker", "worker", "paint-worklet", "audio-worklet", "worklet"]

type script_RemoteReference = script_SharedReference | script_RemoteObjectReference

class script_SharedReference(TypedDict):
    sharedId: script_SharedId
    handle: NotRequired[script_Handle]

class script_RemoteObjectReference(TypedDict):
    handle: script_Handle
    sharedId: NotRequired[script_SharedId]

type script_RemoteValue = script_PrimitiveProtocolValue | script_SymbolRemoteValue | script_ArrayRemoteValue | script_ObjectRemoteValue | script_FunctionRemoteValue | script_RegExpRemoteValue | script_DateRemoteValue | script_MapRemoteValue | script_SetRemoteValue | script_WeakMapRemoteValue | script_WeakSetRemoteValue | script_GeneratorRemoteValue | script_ErrorRemoteValue | script_ProxyRemoteValue | script_PromiseRemoteValue | script_TypedArrayRemoteValue | script_ArrayBufferRemoteValue | script_NodeListRemoteValue | script_HTMLCollectionRemoteValue | script_NodeRemoteValue | script_WindowProxyRemoteValue

type script_ListRemoteValue = list[script_RemoteValue]

type script_MappingRemoteValue = list[tuple[script_RemoteValue | str, script_RemoteValue]]

class script_SymbolRemoteValue(TypedDict):
    type: Literal["symbol"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_ArrayRemoteValue(TypedDict):
    type: Literal["array"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    value: NotRequired[script_ListRemoteValue]

class script_ObjectRemoteValue(TypedDict):
    type: Literal["object"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    value: NotRequired[script_MappingRemoteValue]

class script_FunctionRemoteValue(TypedDict):
    type: Literal["function"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_RegExpRemoteValue(TypedDict):
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    type: NotRequired[Literal["regexp"]]
    value: NotRequired[script_RegExpValue]

class script_DateRemoteValue(TypedDict):
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    type: NotRequired[Literal["date"]]
    value: NotRequired[str]

class script_MapRemoteValue(TypedDict):
    type: Literal["map"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    value: NotRequired[script_MappingRemoteValue]

class script_SetRemoteValue(TypedDict):
    type: Literal["set"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    value: NotRequired[script_ListRemoteValue]

class script_WeakMapRemoteValue(TypedDict):
    type: Literal["weakmap"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_WeakSetRemoteValue(TypedDict):
    type: Literal["weakset"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_GeneratorRemoteValue(TypedDict):
    type: Literal["generator"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_ErrorRemoteValue(TypedDict):
    type: Literal["error"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_ProxyRemoteValue(TypedDict):
    type: Literal["proxy"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_PromiseRemoteValue(TypedDict):
    type: Literal["promise"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_TypedArrayRemoteValue(TypedDict):
    type: Literal["typedarray"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_ArrayBufferRemoteValue(TypedDict):
    type: Literal["arraybuffer"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_NodeListRemoteValue(TypedDict):
    type: Literal["nodelist"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    value: NotRequired[script_ListRemoteValue]

class script_HTMLCollectionRemoteValue(TypedDict):
    type: Literal["htmlcollection"]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    value: NotRequired[script_ListRemoteValue]

class script_NodeRemoteValue(TypedDict):
    type: Literal["node"]
    sharedId: NotRequired[script_SharedId]
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]
    value: NotRequired[script_NodeProperties]

class script_NodeProperties(TypedDict):
    nodeType: int
    childNodeCount: int
    attributes: NotRequired[dict[str, Any]]
    children: NotRequired[list[script_NodeRemoteValue]]
    localName: NotRequired[str]
    mode: NotRequired[Literal["open", "closed"]]
    namespaceURI: NotRequired[str]
    nodeValue: NotRequired[str]
    shadowRoot: NotRequired[script_NodeRemoteValue | None]

class script_WindowProxyRemoteValue(TypedDict):
    type: Literal["window"]
    value: script_WindowProxyProperties
    handle: NotRequired[script_Handle]
    internalId: NotRequired[script_InternalId]

class script_WindowProxyProperties(TypedDict):
    context: browsingContext_BrowsingContext

type script_ResultOwnership = Literal["root", "none"]

class script_SerializationOptions(TypedDict):
    maxDomDepth: NotRequired[int | None]
    maxObjectDepth: NotRequired[int | None]
    includeShadowTree: NotRequired[Literal["none", "open", "all"]]

type script_SharedId = str

class script_StackFrame(TypedDict):
    columnNumber: int
    functionName: str
    lineNumber: int
    url: str

class script_StackTrace(TypedDict):
    callFrames: list[script_StackFrame]

class script_Source(TypedDict):
    realm: script_Realm
    context: NotRequired[browsingContext_BrowsingContext]
    userContext: NotRequired[browser_UserContext]

class script_RealmTarget(TypedDict):
    realm: script_Realm

class script_ContextTarget(TypedDict):
    context: browsingContext_BrowsingContext
    sandbox: NotRequired[str]

type script_Target = script_ContextTarget | script_RealmTarget

class script_AddPreloadScript(TypedDict):
    method: Literal["script.addPreloadScript"]
    params: script_AddPreloadScriptParameters

class script_AddPreloadScriptParameters(TypedDict):
    functionDeclaration: str
    arguments: NotRequired[list[script_ChannelValue]]
    contexts: NotRequired[list[browsingContext_BrowsingContext]]
    userContexts: NotRequired[list[browser_UserContext]]
    sandbox: NotRequired[str]

class script_AddPreloadScriptResult(TypedDict):
    script: script_PreloadScript

class script_Disown(TypedDict):
    method: Literal["script.disown"]
    params: script_DisownParameters

class script_DisownParameters(TypedDict):
    handles: list[script_Handle]
    target: script_Target

type script_DisownResult = EmptyResult

class script_CallFunction(TypedDict):
    method: Literal["script.callFunction"]
    params: script_CallFunctionParameters

class script_CallFunctionParameters(TypedDict):
    functionDeclaration: str
    awaitPromise: bool
    target: script_Target
    arguments: NotRequired[list[script_LocalValue]]
    resultOwnership: NotRequired[script_ResultOwnership]
    serializationOptions: NotRequired[script_SerializationOptions]
    this: NotRequired[script_LocalValue]
    userActivation: NotRequired[bool]

type script_CallFunctionResult = script_EvaluationResult

class script_Evaluate(TypedDict):
    method: Literal["script.evaluate"]
    params: script_EvaluateParameters

class script_EvaluateParameters(TypedDict):
    expression: str
    target: script_Target
    awaitPromise: bool
    resultOwnership: NotRequired[script_ResultOwnership]
    serializationOptions: NotRequired[script_SerializationOptions]
    userActivation: NotRequired[bool]

type script_EvaluateResult = script_EvaluationResult

class script_GetRealms(TypedDict):
    method: Literal["script.getRealms"]
    params: script_GetRealmsParameters

class script_GetRealmsParameters(TypedDict):
    context: NotRequired[browsingContext_BrowsingContext]
    type: NotRequired[script_RealmType]

class script_GetRealmsResult(TypedDict):
    realms: list[script_RealmInfo]

class script_RemovePreloadScript(TypedDict):
    method: Literal["script.removePreloadScript"]
    params: script_RemovePreloadScriptParameters

class script_RemovePreloadScriptParameters(TypedDict):
    script: script_PreloadScript

type script_RemovePreloadScriptResult = EmptyResult

class script_Message(TypedDict):
    method: Literal["script.message"]
    params: script_MessageParameters

class script_MessageParameters(TypedDict):
    channel: script_Channel
    data: script_RemoteValue
    source: script_Source

class script_RealmCreated(TypedDict):
    method: Literal["script.realmCreated"]
    params: script_RealmInfo

class script_RealmDestroyed(TypedDict):
    method: Literal["script.realmDestroyed"]
    params: script_RealmDestroyedParameters

class script_RealmDestroyedParameters(TypedDict):
    realm: script_Realm

type StorageCommand = storage_DeleteCookies | storage_GetCookies | storage_SetCookie

type StorageResult = storage_DeleteCookiesResult | storage_GetCookiesResult | storage_SetCookieResult

class storage_PartitionKey(TypedDict):
    userContext: NotRequired[str]
    sourceOrigin: NotRequired[str]

class storage_GetCookies(TypedDict):
    method: Literal["storage.getCookies"]
    params: storage_GetCookiesParameters

class storage_CookieFilter(TypedDict):
    name: NotRequired[str]
    value: NotRequired[network_BytesValue]
    domain: NotRequired[str]
    path: NotRequired[str]
    size: NotRequired[int]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[network_SameSite]
    expiry: NotRequired[int]

class storage_BrowsingContextPartitionDescriptor(TypedDict):
    type: Literal["context"]
    context: browsingContext_BrowsingContext

class storage_StorageKeyPartitionDescriptor(TypedDict):
    type: Literal["storageKey"]
    userContext: NotRequired[str]
    sourceOrigin: NotRequired[str]

type storage_PartitionDescriptor = storage_BrowsingContextPartitionDescriptor | storage_StorageKeyPartitionDescriptor

class storage_GetCookiesParameters(TypedDict):
    filter: NotRequired[storage_CookieFilter]
    partition: NotRequired[storage_PartitionDescriptor]

class storage_GetCookiesResult(TypedDict):
    cookies: list[network_Cookie]
    partitionKey: storage_PartitionKey

class storage_SetCookie(TypedDict):
    method: Literal["storage.setCookie"]
    params: storage_SetCookieParameters

class storage_PartialCookie(TypedDict):
    name: str
    value: network_BytesValue
    domain: str
    path: NotRequired[str]
    httpOnly: NotRequired[bool]
    secure: NotRequired[bool]
    sameSite: NotRequired[network_SameSite]
    expiry: NotRequired[int]

class storage_SetCookieParameters(TypedDict):
    cookie: storage_PartialCookie
    partition: NotRequired[storage_PartitionDescriptor]

class storage_SetCookieResult(TypedDict):
    partitionKey: storage_PartitionKey

class storage_DeleteCookies(TypedDict):
    method: Literal["storage.deleteCookies"]
    params: storage_DeleteCookiesParameters

class storage_DeleteCookiesParameters(TypedDict):
    filter: NotRequired[storage_CookieFilter]
    partition: NotRequired[storage_PartitionDescriptor]

class storage_DeleteCookiesResult(TypedDict):
    partitionKey: storage_PartitionKey

type LogEvent = log_EntryAdded

type log_Level = Literal["debug", "info", "warn", "error"]

type log_Entry = log_GenericLogEntry | log_ConsoleLogEntry | log_JavascriptLogEntry

class log_BaseLogEntry(TypedDict):
    level: log_Level
    source: script_Source
    text: str | None
    timestamp: int
    stackTrace: NotRequired[script_StackTrace]

class log_GenericLogEntry(TypedDict):
    type: str
    level: NotRequired[log_Level]
    source: NotRequired[script_Source]
    text: NotRequired[str | None]
    timestamp: NotRequired[int]
    stackTrace: NotRequired[script_StackTrace]

class log_ConsoleLogEntry(TypedDict):
    type: Literal["console"]
    method: str
    args: list[script_RemoteValue]
    level: NotRequired[log_Level]
    source: NotRequired[script_Source]
    text: NotRequired[str | None]
    timestamp: NotRequired[int]
    stackTrace: NotRequired[script_StackTrace]

class log_JavascriptLogEntry(TypedDict):
    type: Literal["javascript"]
    level: NotRequired[log_Level]
    source: NotRequired[script_Source]
    text: NotRequired[str | None]
    timestamp: NotRequired[int]
    stackTrace: NotRequired[script_StackTrace]

class log_EntryAdded(TypedDict):
    method: Literal["log.entryAdded"]
    params: log_Entry

type InputCommand = input_PerformActions | input_ReleaseActions | input_SetFiles

type InputResult = input_PerformActionsResult | input_ReleaseActionsResult | input_SetFilesResult

type InputEvent = input_FileDialogOpened

class input_ElementOrigin(TypedDict):
    type: Literal["element"]
    element: script_SharedReference

class input_PerformActions(TypedDict):
    method: Literal["input.performActions"]
    params: input_PerformActionsParameters

class input_PerformActionsParameters(TypedDict):
    context: browsingContext_BrowsingContext
    actions: list[input_SourceActions]

type input_SourceActions = input_NoneSourceActions | input_KeySourceActions | input_PointerSourceActions | input_WheelSourceActions

class input_NoneSourceActions(TypedDict):
    type: Literal["none"]
    id: str
    actions: list[input_NoneSourceAction]

type input_NoneSourceAction = input_PauseAction

class input_KeySourceActions(TypedDict):
    type: Literal["key"]
    id: str
    actions: list[input_KeySourceAction]

type input_KeySourceAction = input_PauseAction | input_KeyDownAction | input_KeyUpAction

class input_PointerSourceActions(TypedDict):
    type: Literal["pointer"]
    id: str
    parameters: NotRequired[input_PointerParameters]
    actions: list[input_PointerSourceAction]

type input_PointerType = Literal["mouse", "pen", "touch"]

class input_PointerParameters(TypedDict):
    pointerType: NotRequired[input_PointerType]

type input_PointerSourceAction = input_PauseAction | input_PointerDownAction | input_PointerUpAction | input_PointerMoveAction

class input_WheelSourceActions(TypedDict):
    type: Literal["wheel"]
    id: str
    actions: list[input_WheelSourceAction]

type input_WheelSourceAction = input_PauseAction | input_WheelScrollAction

class input_PauseAction(TypedDict):
    type: Literal["pause"]
    duration: NotRequired[int]

class input_KeyDownAction(TypedDict):
    type: Literal["keyDown"]
    value: str

class input_KeyUpAction(TypedDict):
    type: Literal["keyUp"]
    value: str

class input_PointerUpAction(TypedDict):
    type: Literal["pointerUp"]
    button: int

class input_PointerDownAction(TypedDict):
    type: Literal["pointerDown"]
    button: int
    width: NotRequired[int]
    height: NotRequired[int]
    pressure: NotRequired[int]
    tangentialPressure: NotRequired[int]
    twist: NotRequired[int]
    altitudeAngle: NotRequired[int]
    azimuthAngle: NotRequired[int]

class input_PointerMoveAction(TypedDict):
    type: Literal["pointerMove"]
    x: float
    y: float
    duration: NotRequired[int]
    origin: NotRequired[input_Origin]
    width: NotRequired[int]
    height: NotRequired[int]
    pressure: NotRequired[int]
    tangentialPressure: NotRequired[int]
    twist: NotRequired[int]
    altitudeAngle: NotRequired[int]
    azimuthAngle: NotRequired[int]

class input_WheelScrollAction(TypedDict):
    type: Literal["scroll"]
    x: int
    y: int
    deltaX: int
    deltaY: int
    duration: NotRequired[int]
    origin: NotRequired[input_Origin]

class input_PointerCommonProperties(TypedDict):
    width: NotRequired[int]
    height: NotRequired[int]
    pressure: NotRequired[int]
    tangentialPressure: NotRequired[int]
    twist: NotRequired[int]
    altitudeAngle: NotRequired[int]
    azimuthAngle: NotRequired[int]

type input_Origin = Literal["viewport"] | Literal["pointer"] | input_ElementOrigin

type input_PerformActionsResult = EmptyResult

class input_ReleaseActions(TypedDict):
    method: Literal["input.releaseActions"]
    params: input_ReleaseActionsParameters

class input_ReleaseActionsParameters(TypedDict):
    context: browsingContext_BrowsingContext

type input_ReleaseActionsResult = EmptyResult

class input_SetFiles(TypedDict):
    method: Literal["input.setFiles"]
    params: input_SetFilesParameters

class input_SetFilesParameters(TypedDict):
    context: browsingContext_BrowsingContext
    element: script_SharedReference
    files: list[str]

type input_SetFilesResult = EmptyResult

class input_FileDialogOpened(TypedDict):
    method: Literal["input.fileDialogOpened"]
    params: input_FileDialogInfo

class input_FileDialogInfo(TypedDict):
    context: browsingContext_BrowsingContext
    userContext: NotRequired[browser_UserContext]
    element: NotRequired[script_SharedReference]
    multiple: bool

type WebExtensionCommand = webExtension_Install | webExtension_Uninstall

type WebExtensionResult = webExtension_InstallResult | webExtension_UninstallResult

type webExtension_Extension = str

class webExtension_Install(TypedDict):
    method: Literal["webExtension.install"]
    params: webExtension_InstallParameters

class webExtension_InstallParameters(TypedDict):
    extensionData: webExtension_ExtensionData

type webExtension_ExtensionData = webExtension_ExtensionArchivePath | webExtension_ExtensionBase64Encoded | webExtension_ExtensionPath

class webExtension_ExtensionPath(TypedDict):
    type: Literal["path"]
    path: str

class webExtension_ExtensionArchivePath(TypedDict):
    type: Literal["archivePath"]
    path: str

class webExtension_ExtensionBase64Encoded(TypedDict):
    type: Literal["base64"]
    value: str

class webExtension_InstallResult(TypedDict):
    extension: webExtension_Extension

class webExtension_Uninstall(TypedDict):
    method: Literal["webExtension.uninstall"]
    params: webExtension_UninstallParameters

class webExtension_UninstallParameters(TypedDict):
    extension: webExtension_Extension

type webExtension_UninstallResult = EmptyResult
