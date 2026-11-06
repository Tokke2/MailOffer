/* Branded GUI host for the installed shared CPython, not a Python child process.
 * Copyright 2026 Rickard Längkvist. No bundled runtime or virtual environment.
 */
#include <windows.h>
#include <shellapi.h>
#include <wchar.h>
#include <stdio.h>

static int fail(const wchar_t *message) {
    MessageBoxW(NULL, message, L"MailOffer", MB_OK | MB_ICONERROR);
    return 1;
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR raw, int show) {
    static wchar_t root[32768], script[32768], host[32768], command[32768];
    DWORD size = GetModuleFileNameW(NULL, root, 32768);
    if (!size || size >= 32768) return 1;
    wchar_t *slash = wcsrchr(root, L'\\');
    if (!slash) return 1;
    *slash = 0;
    HANDLE focus = CreateEventW(NULL, FALSE, FALSE, L"Local\\RickardLangkvist.MailOffer.Focus");
    HANDLE owner = CreateFileMappingW(INVALID_HANDLE_VALUE, NULL, PAGE_READWRITE, 0, sizeof(DWORD), L"Local\\RickardLangkvist.MailOffer.Owner");
    DWORD *pid = owner ? MapViewOfFile(owner, FILE_MAP_ALL_ACCESS, 0, 0, sizeof(DWORD)) : NULL;
    HANDLE mutex = CreateMutexW(NULL, TRUE, L"Local\\RickardLangkvist.MailOffer.Host");
    DWORD mutex_error = GetLastError();
    if (!focus || !mutex || !pid) return fail(L"Kunde inte skapa enkelinstans-skyddet.");
    if (mutex_error == ERROR_ALREADY_EXISTS) {
        if (*pid) AllowSetForegroundWindow(*pid);
        SetEvent(focus);
        UnmapViewOfFile(pid); CloseHandle(owner); CloseHandle(mutex); CloseHandle(focus);
        return 0;
    }
    *pid = GetCurrentProcessId();
    SetCurrentDirectoryW(root);
    swprintf(script, 32768, L"%ls\\tools\\python_bootstrap.vbs", root);
    if (GetFileAttributesW(script) == INVALID_FILE_ATTRIBUTES) return fail(L"Startfiler saknas. Packa upp hela MailOffer-mappen.");
    size = GetSystemDirectoryW(host, 32768);
    if (!size || size + 13 >= 32768) return 1;
    wcscat(host, L"\\wscript.exe");
    swprintf(command, 32768, L"\"%ls\" //B //nologo \"%ls\"", host, script);
    STARTUPINFOW startup = {0}; PROCESS_INFORMATION process = {0}; startup.cb = sizeof(startup);
    if (!CreateProcessW(host, command, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, root, &startup, &process)) return fail(L"Kunde inte starta Python-kontrollen.");
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD result = 1; GetExitCodeProcess(process.hProcess, &result);
    CloseHandle(process.hThread); CloseHandle(process.hProcess);
    if (result) return fail(L"Python-kontrollen misslyckades. Se logs\\python-startup.log. Ingen extra Python-miljo skapas.");

    static wchar_t runtime[32768], python[32768], home[32768], dll[32768], pattern[32768];
    swprintf(runtime, 32768, L"%ls\\logs\\python-runtime.txt", root);
    FILE *file = _wfopen(runtime, L"rb");
    if (!file) return fail(L"Kontrollerad Python saknas.");
    size_t n = fread(python, sizeof(wchar_t), 32767, file); fclose(file); python[n] = 0;
    if (n && python[0] == 0xFEFF) memmove(python, python + 1, n * sizeof(wchar_t));
    if (!n || GetFileAttributesW(python) == INVALID_FILE_ATTRIBUTES) return fail(L"Python-sokvagen ar ogiltig.");
    wcscpy(home, python); slash = wcsrchr(home, L'\\');
    if (!slash) return 1; *slash = 0;
    swprintf(pattern, 32768, L"%ls\\python3*.dll", home);
    WIN32_FIND_DATAW found; HANDLE search = FindFirstFileW(pattern, &found);
    BOOL matched = FALSE;
    if (search != INVALID_HANDLE_VALUE) {
        do {
            const wchar_t *p = found.cFileName + 7;
            if (*p < L'0' || *p > L'9') continue;
            while (*p >= L'0' && *p <= L'9') ++p;
            if (!wcscmp(p, L".dll")) {
                swprintf(dll, 32768, L"%ls\\%ls", home, found.cFileName);
                matched = TRUE; break;
            }
        } while (FindNextFileW(search, &found));
        FindClose(search);
    }
    if (!matched) return fail(L"CPython DLL saknas. Delad standard-CPython x64 kravs.");
    HMODULE library = LoadLibraryExW(dll, NULL, LOAD_WITH_ALTERED_SEARCH_PATH);
    if (!library) return fail(L"Kunde inte ladda installerad CPython. MailOffer.exe kraver Python x64.");
    typedef void (__cdecl *SetWide)(const wchar_t *);
    typedef int (__cdecl *PythonMain)(int, wchar_t **);
    SetWide set_program = (SetWide)GetProcAddress(library, "Py_SetProgramName");
    SetWide set_home = (SetWide)GetProcAddress(library, "Py_SetPythonHome");
    PythonMain python_main = (PythonMain)GetProcAddress(library, "Py_Main");
    if (!set_program || !set_home || !python_main) return fail(L"Python-versionen saknar nodvandigt host-API.");
    SetEnvironmentVariableW(L"MAILOFFER_STARTUP_READY", L"1");
    SetEnvironmentVariableW(L"MAILOFFER_NATIVE_HOST", L"1");
    set_program(python); set_home(home);
    int count = 0; LPWSTR *args = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!args) return 1;
    wchar_t **python_args = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, sizeof(wchar_t *) * (count + 2));
    if (!python_args) return 1;
    swprintf(script, 32768, L"%ls\\main.pyw", root);
    python_args[0] = python; python_args[1] = script;
    for (int i = 1; i < count; ++i) python_args[i + 1] = args[i];
    int code = python_main(count + 1, python_args);
    HeapFree(GetProcessHeap(), 0, python_args); LocalFree(args);
    *pid = 0; UnmapViewOfFile(pid); CloseHandle(owner);
    ReleaseMutex(mutex); CloseHandle(mutex); CloseHandle(focus);
    /* Python/Qt extension DLLs can register exit callbacks. Keep them loaded. */
    return code;
}
