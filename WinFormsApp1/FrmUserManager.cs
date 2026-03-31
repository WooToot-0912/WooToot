using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using WinFormsApp1.Models;
using WinFormsApp1.Service;
using WinFormsApp1.ServiceImpl;

namespace WinFormsApp1
{
    public partial class FrmUserManager : Form
    {
        //判断登入的用户的权限
        //增删改查用户得有对应的权限
        //加载所有用户信息

        /// <summary>
        /// 用户管理服务接口
        /// </summary>
        private IUserDataManagerService userDataManagerService { get; set; }

        public FrmUserManager()
        {
            InitializeComponent();
        }

        private void button5_Click(object sender, EventArgs e)
        {
            this.Close();
        }

        private void FrmUserManager_Load(object sender, EventArgs e)
        {
            userDataManagerService = new UserDataManagerServiceImpl();

            InitUser();

        }

        private void InitUser()
        {
            //获取所有用户数据
            List<User> users = userDataManagerService.GetUsers();

            users.Insert(0, new User { NickName = "匿名", UserName = "用户名", Email = "邮箱", Phone = "手机号", PassWord = "密码" });

            //绑定数据到listBox DataSource 绑定集合对象
            listBox1.DataSource = users;


            //DisplayMember:要显示的属性
            listBox1.DisplayMember = "DisPlayInfo";
            //给程序员看的隐藏属性
            listBox1.ValueMember = "Id";
        }

        private void button2_Click(object sender, EventArgs e)
        {
            if (listBox1.SelectedIndex == 0)
            {
                MessageBox.Show("请选择用户,删除失败！");
                return;

            }

            userDataManagerService.DeleteById(listBox1.SelectedValue.ToString());
            MessageBox.Show("删除成功！");
            InitUser();
        }
    }
}
