using System.Runtime.CompilerServices;
using WinFormsApp1.Models;
using WinFormsApp1.Service;
using WinFormsApp1.ServiceImpl;
using WinFormsApp1.Utils;

namespace WinFormsApp1
{
    public partial class Form1 : Form
    {
        /// <summary>
        /// 用户服务接口
        /// </summary>
        private IUserService userService { get; set; }

        /// <summary>
        /// 用户本地服务接口
        /// </summary>
        public IUserDataService userDataService { get; set; }

        /// <summary>
        /// 本地用户数据
        /// </summary>
        public UserDb userDb { get; set; }

        private void Form1_Load(object sender, EventArgs e)
        {
            //注入用户服务接口
            userService = new UserServiceImpl();

            userDataService = new UserDataServiceImpl();

            userDataService.GetUserList();
            userDb = UserDb.GetUserDb();
            userDb.Users = userDataService.GetUserList(); //在程序刚开始运行时，获取所有用户

            //保存了用户信息
            User user = userService.GetRememberUser();
            if (user.UserName == null)
            {
                return;
            }
            else if(userService.Login(user))
            {
                MessageBox.Show("登录成功！");

                //1.把窗体  hide 隐藏
                //2.模态窗体
                //FormMain Frm = new FormMain();
                //Frm.Show();
                //MyLog<Form1>.LogDebug($"{DateTime.Now}:  登录成功");
                //修改当前窗体的返回值
                this.DialogResult = DialogResult.OK;

            }
            else
            {
                MessageBox.Show("登录失败！");
                //MyLog<Form1>.LogDebug($"{DateTime.Now}:  登录失败");
                ///清空密码
                txtPwd.Clear();
            }
        
        }

        //1.勾选且登陆成功
        //2.记录账号和密码到本地
        //3.Form1事件     读取过来   ----> 登入逻辑进行登入 登入成功直接进入主页面 
        //登录失败

        public Form1()
        {
            InitializeComponent();
        }
        /// <summary>
        /// 退出 
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void button3_Click(object sender, EventArgs e)
        {
            //退出
            this.Close();
        }


        //项目分层：

        //为了项目更好的迭代，让项目不在冗余
        //如果写小项目或上位机项目 采用这种分成
        //业务逻辑层：服务   面向接口编程Service层  规则：什么名字Service  接口  定义这个业务逻辑要实现的函数
        //业务逻辑实现层：  取名：ServiceImpl 存放接口的实现类
        //实体层：模型层：  存放实体类对象 Models Entity
        //工具类：utils 什么工具utils  static方法

        /// <summary>
        /// 登录
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void button1_Click(object sender, EventArgs e)
        {
            //1.获取账号和密码
            //string userName = txtUserName.Text.Trim();
            //string pwd = txtPwd.Text.Trim();

            //封装用户对象
            User user = new User();
            user.UserName = txtUserName.Text.Trim();
            user.PassWord = txtPwd.Text.Trim();

            if (userService.Login(user))
            {
                MessageBox.Show("登录成功！");

                //1.把窗体  hide 隐藏
                //2.模态窗体
                //FormMain Frm = new FormMain();
                //Frm.Show();

                if (ckLogin.Checked)
                {
                    //1.勾选且登陆成功
                    //2.记录账号和密码到本地
                    //3.Form1事件     读取过来   ----> 登入逻辑进行登入 登入成功直接进入主页面 
                    //登录失败
                    userService.RememberMe(user);
                    //MyLog<Form1>.LogDebug("记录用户信息成功");
                }

                //MyLog<Form1>.LogDebug($"{DateTime.Now}:  登录成功");
                //修改当前窗体的返回值
                this.DialogResult = DialogResult.OK;


            }
            else
            {
                MessageBox.Show("登录失败！");
                //MyLog<Form1>.LogDebug($"{DateTime.Now}:  登录失败");
                ///清空密码
                txtPwd.Clear();
            }



        }


        /// <summary>
        /// 文本改变事件
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void txtUserName_TextChanged(object sender, EventArgs e)
        {
            //获取文本框中的内容
            string userName = txtUserName.Text.Trim();
            string pwd = txtPwd.Text.Trim();
            if (UserCheckUtil.CheckUSerInput(userName) || UserCheckUtil.CheckUSerInput(pwd))
            {
                this.btnLogin.Enabled = false;
                return;
            }

            this.btnLogin.Enabled = true;

        }






        /// <summary>
        /// 
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void txtPwd_TextChanged(object sender, EventArgs e)
        {
            //获取文本框中的内容
            string userName = txtUserName.Text.Trim();
            string pwd = txtPwd.Text.Trim();
            if (UserCheckUtil.CheckUSerInput(userName) || UserCheckUtil.CheckUSerInput(pwd))
            {
                this.btnLogin.Enabled = false;
                return;
            }

            this.btnLogin.Enabled = true;
        }

        private void btnRegister_Click(object sender, EventArgs e)
        {
            FormRegister frm = new FormRegister();
            frm.FormClosed += Frm_FormClosed;
            this.Hide();
            frm.ShowDialog();
        }

        private void Frm_FormClosed(object? sender, FormClosedEventArgs e)
        {
            this.Show();
        }
    }
}
