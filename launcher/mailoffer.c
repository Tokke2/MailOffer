/* MailOffer GUI launcher. Build instructions: tools/build_launcher.py.
 * No Python executable icon, console, shell command expansion or elevation.
 * Copyright 2026 Rickard Längkvist.
 */
#include <windows.h>
#include <shellapi.h>
#include <wchar.h>
#include <stdio.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR raw, int show) {
    wchar_t directory[32768], script[32768], host[32768], command[32768];
    DWORD length = GetModuleFileNameW(NULL, directory, 32768);
    if (!length || length >= 32768) return 1;
    wchar_t *slash = wcsrchr(directory, L'\\');
    if (!slash) return 1;
    *slash = 0;
    if (swprintf(script, 32768, L"%ls\\Starta EmailApp.vbs", directory) < 0) return 1;
    if (GetFileAttributesW(script) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL, L"Starta EmailApp.vbs saknas. Packa upp hela MailOffer, inte bara exe-filen.", L"MailOffer", MB_OK | MB_ICONERROR);
        return 1;
    }
    UINT size = GetSystemDirectoryW(host, 32768);
    if (!size || size + 13 >= 32768) return 1;
    wcscat(host, L"\\wscript.exe");
    int count = 0;
    LPWSTR *args = CommandLineToArgvW(GetCommandLineW(), &count);
    if (!args) return 1;
    BOOL background = FALSE;
    for (int i = 1; i < count; ++i) {
        if (!wcscmp(args[i], L"--background") || !wcscmp(args[i], L"--minimized")) background = TRUE;
        else {
            LocalFree(args);
            MessageBoxW(NULL, L"Okant startargument. Anvand --background for bakgrundsstart.", L"MailOffer", MB_OK | MB_ICONERROR);
            return 2;
        }
    }
    LocalFree(args);
    if (swprintf(command, 32768, L"\"%ls\" //B //nologo \"%ls\"%ls", host, script, background ? L" --background" : L"") < 0) return 1;
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(host, command, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, directory, &startup, &process)) {
        MessageBoxW(NULL, L"Kunde inte starta MailOffer. Kontrollera att Windows Script Host ar tillatet.", L"MailOffer", MB_OK | MB_ICONERROR);
        return 1;
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return 0;
}
