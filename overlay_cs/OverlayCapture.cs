using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

internal static class OverlayCapture
{
    [StructLayout(LayoutKind.Sequential)]
    private struct Rect
    {
        internal int Left;
        internal int Top;
        internal int Right;
        internal int Bottom;
    }

    private delegate bool EnumWindowsProc(IntPtr hwnd, IntPtr parameter);

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr parameter);

    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint processId);

    [DllImport("user32.dll")]
    private static extern bool IsWindowVisible(IntPtr hwnd);

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    private static extern void mouse_event(
        uint flags, uint dx, uint dy, uint data, UIntPtr extraInfo);

    [DllImport("user32.dll")]
    private static extern IntPtr SendMessage(IntPtr hwnd, int message, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(IntPtr hwnd, StringBuilder text, int count);

    [DllImport("dwmapi.dll")]
    private static extern int DwmGetWindowAttribute(
        IntPtr hwnd, int attribute, out Rect value, int valueSize);

    private static IntPtr FindWindow(uint targetProcess, string titleContains)
    {
        IntPtr found = IntPtr.Zero;
        long largest = 0;
        EnumWindows(delegate(IntPtr hwnd, IntPtr parameter)
        {
            uint process;
            GetWindowThreadProcessId(hwnd, out process);
            if (process != targetProcess || !IsWindowVisible(hwnd)) return true;
            if (!string.IsNullOrEmpty(titleContains))
            {
                StringBuilder title = new StringBuilder(256);
                GetWindowText(hwnd, title, title.Capacity);
                if (!title.ToString().Contains(titleContains)) return true;
            }
            Rect rect;
            if (DwmGetWindowAttribute(hwnd, 9, out rect, Marshal.SizeOf(typeof(Rect))) != 0)
                return true;
            long area = (long)(rect.Right - rect.Left) * (rect.Bottom - rect.Top);
            if (area > largest)
            {
                largest = area;
                found = hwnd;
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    internal static int Main(string[] args)
    {
        if (args.Length < 1) return 2;
        int delay = args.Length > 1 ? Convert.ToInt32(args[1]) : 0;
        if (delay > 0) Thread.Sleep(delay);
        Process[] processes = Process.GetProcessesByName("SystemAudioOverlay");
        if (processes.Length == 0) return 3;
        string title = args.Length > 2 ? args[2] : "";
        if (title == "--hit-test")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            Rect testRect;
            if (overlay == IntPtr.Zero || DwmGetWindowAttribute(
                overlay, 9, out testRect, Marshal.SizeOf(typeof(Rect))) != 0) return 6;
            int x = testRect.Right - 2;
            int y = testRect.Bottom - 2;
            long packed = ((long)(y & 0xFFFF) << 16) | (uint)(x & 0xFFFF);
            int result = SendMessage(overlay, 0x0084, IntPtr.Zero, new IntPtr(packed)).ToInt32();
            Console.WriteLine("WM_NCHITTEST bottom-right=" + result);
            return result == 17 ? 0 : 7;
        }
        if (title == "--boss-toggle")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            if (overlay == IntPtr.Zero) return 6;
            SendMessage(overlay, 0x0312, new IntPtr(0xA52), IntPtr.Zero);
            Thread.Sleep(250);
            Console.WriteLine("boss hotkey message sent");
            return 0;
        }
        if (title == "--graceful-exit")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            if (overlay == IntPtr.Zero) return 6;
            SendMessage(overlay, 0x8030, IntPtr.Zero, IntPtr.Zero);
            Console.WriteLine("graceful exit requested");
            return 0;
        }
        if (title == "--scroll-up" || title == "--scroll-down")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            Rect scrollRect;
            if (overlay == IntPtr.Zero || DwmGetWindowAttribute(
                overlay, 9, out scrollRect, Marshal.SizeOf(typeof(Rect))) != 0) return 6;
            SetCursorPos(
                (scrollRect.Left + scrollRect.Right) / 2,
                (scrollRect.Top + scrollRect.Bottom) / 2);
            uint delta = title == "--scroll-up" ? 120u : unchecked((uint)-120);
            for (int index = 0; index < 8; index++)
            {
                mouse_event(0x0800, 0, 0, delta, UIntPtr.Zero);
                Thread.Sleep(45);
            }
            Thread.Sleep(250);
            Console.WriteLine(title.Substring(2) + " sent");
            return 0;
        }
        if (title == "--drag-move")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            Rect before;
            if (overlay == IntPtr.Zero || DwmGetWindowAttribute(
                overlay, 9, out before, Marshal.SizeOf(typeof(Rect))) != 0) return 6;
            int startX = (before.Left + before.Right) / 2;
            int startY = (before.Top + before.Bottom) / 2;
            SetCursorPos(startX, startY);
            Thread.Sleep(150);
            mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
            for (int step = 1; step <= 10; step++)
            {
                SetCursorPos(startX + step * 8, startY - step * 3);
                Thread.Sleep(35);
            }
            mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
            Thread.Sleep(500);
            Rect after;
            if (DwmGetWindowAttribute(overlay, 9, out after, Marshal.SizeOf(typeof(Rect))) != 0) return 8;
            Console.WriteLine(string.Format(
                "drag move ({0},{1}) -> ({2},{3})",
                before.Left, before.Top, after.Left, after.Top));
            return before.Left != after.Left || before.Top != after.Top ? 0 : 9;
        }
        if (title == "--drag-resize")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            Rect before;
            if (overlay == IntPtr.Zero || DwmGetWindowAttribute(
                overlay, 9, out before, Marshal.SizeOf(typeof(Rect))) != 0) return 6;
            int startX = before.Right - 10;
            int startY = before.Bottom - 10;
            SetCursorPos(startX, startY);
            Thread.Sleep(150);
            mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
            for (int step = 1; step <= 10; step++)
            {
                SetCursorPos(startX + step * 10, startY + step * 8);
                Thread.Sleep(35);
            }
            mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
            Thread.Sleep(700);
            Rect after;
            if (DwmGetWindowAttribute(overlay, 9, out after, Marshal.SizeOf(typeof(Rect))) != 0) return 8;
            int beforeWidth = before.Right - before.Left;
            int beforeHeight = before.Bottom - before.Top;
            int afterWidth = after.Right - after.Left;
            int afterHeight = after.Bottom - after.Top;
            Console.WriteLine(string.Format(
                "drag resize {0}x{1} -> {2}x{3}",
                beforeWidth, beforeHeight, afterWidth, afterHeight));
            return afterWidth > beforeWidth && afterHeight > beforeHeight ? 0 : 9;
        }
        if (title == "--click-reset")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            Rect overlayRect;
            if (overlay == IntPtr.Zero || DwmGetWindowAttribute(
                overlay, 9, out overlayRect, Marshal.SizeOf(typeof(Rect))) != 0) return 6;
            SetCursorPos((overlayRect.Left + overlayRect.Right) / 2, (overlayRect.Top + overlayRect.Bottom) / 2);
            Thread.Sleep(700);
            IntPtr controls = FindWindow((uint)processes[0].Id, "字幕位置锁");
            Rect controlRect;
            if (controls == IntPtr.Zero || DwmGetWindowAttribute(
                controls, 9, out controlRect, Marshal.SizeOf(typeof(Rect))) != 0) return 10;
            SetCursorPos(controlRect.Left + 17, (controlRect.Top + controlRect.Bottom) / 2);
            Thread.Sleep(120);
            mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero);
            Thread.Sleep(80);
            mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
            Thread.Sleep(350);
            Console.WriteLine("reset button clicked");
            return 0;
        }
        if (title == "--hover-lock" || title == "--hover-frame")
        {
            IntPtr overlay = FindWindow((uint)processes[0].Id, "系统声音实时字幕 Overlay");
            Rect overlayRect;
            if (overlay == IntPtr.Zero || DwmGetWindowAttribute(
                overlay, 9, out overlayRect, Marshal.SizeOf(typeof(Rect))) != 0) return 6;
            if (title == "--hover-lock")
                SetCursorPos(overlayRect.Right - 26, overlayRect.Top + 18);
            else
                SetCursorPos((overlayRect.Left + overlayRect.Right) / 2, (overlayRect.Top + overlayRect.Bottom) / 2);
            Thread.Sleep(700);
            title = title == "--hover-lock" ? "字幕位置锁" : "系统声音实时字幕 Overlay";
        }
        IntPtr hwnd = FindWindow((uint)processes[0].Id, title);
        if (hwnd == IntPtr.Zero) return 4;
        Rect rect;
        if (DwmGetWindowAttribute(hwnd, 9, out rect, Marshal.SizeOf(typeof(Rect))) != 0) return 5;
        int width = rect.Right - rect.Left;
        int height = rect.Bottom - rect.Top;
        using (Bitmap bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb))
        using (Graphics graphics = Graphics.FromImage(bitmap))
        {
            graphics.CopyFromScreen(rect.Left, rect.Top, 0, 0, new Size(width, height));
            bitmap.Save(args[0], ImageFormat.Png);
        }
        Console.WriteLine(string.Format("captured {0}x{1} {2}", width, height, args[0]));
        return 0;
    }
}
