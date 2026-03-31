namespace WinFormsApp1
{
    internal static class Program
    {
        /// <summary>
        ///  The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            // To customize application configuration such as set high DPI settings or default font,
            // see https://aka.ms/applicationconfiguration.
            ApplicationConfiguration.Initialize();
         

            //模态窗体
            Form1 frmLogin = new Form1();
            DialogResult dr = frmLogin.ShowDialog();
            //ShowDialog:阻断后面代码的运行 知道这个代码运行完成
            //Application.Run(new FrmUserManager());
            if (dr == DialogResult.OK)
            {
                //1.RUN跑的是主窗体 主窗体一个是FormMain
                Application.Run(new Form1());
            }


        }
    }
}