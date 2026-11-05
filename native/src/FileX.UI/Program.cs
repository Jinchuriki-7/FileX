using System.Threading;

namespace FileX.UI;

public static class Program
{
    private const string MutexName = "Global\\FileX_SingleInstance_Mutex";

    [STAThread]
    public static void Main(string[] args)
    {
        using var mutex = new Mutex(true, MutexName, out bool isNewInstance);

        if (!isNewInstance)
        {
            // Already running
            return;
        }

        var app = new App();
        app.InitializeComponent();
        app.Run();
    }
}

