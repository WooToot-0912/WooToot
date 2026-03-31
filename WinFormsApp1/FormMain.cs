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
    public partial class FormMain : Form
    {
        /// <summary>
        /// 本地用户服务
        /// </summary>
        private IUserDataService UserDataService { get; set; }

        private User user { get; set; }

        public FormMain()
        {
            InitializeComponent();
        }

        private void FormMain_Load(object sender, EventArgs e)
        {
            this.btnUpdate.Enabled = false;
            UserDataService = new UserDataServiceImpl();
            // 调用全局本地用户信息
            UserDataService.GetUserById(GlobalUser.Id);

            MessageBox.Show($"欢迎{user.NickName}进入主页面");
            TxtEmail.Text = user.Email;
            TxtNickName.Text = user.NickName;
            TxtPassWord.Text = user.PassWord;
            TxtUserName.Text = user.UserName;
            TxtPhone.Text = user.Phone;
        }

        private void TxtNickName_TextChanged(object sender, EventArgs e)
        {
            if (WatchUpdate())
            {
                this.btnUpdate.Enabled = true;
            }
            else
            {
                this.btnUpdate.Enabled = false;
            }
        }
        private bool WatchUpdate()
        {
            User user1 = new User();
            user1.Email = TxtEmail.Text;
            user1.NickName = TxtNickName.Text;
            user1.PassWord = TxtPassWord.Text;
            user1.Phone = TxtPhone.Text;
            if (user1.Equals(user))
            {
                return false;
            }
            return true;
        }

        private void TxtPassWord_TextChanged(object sender, EventArgs e)
        {
            if (WatchUpdate())
            {
                this.btnUpdate.Enabled = true;
            }
            else
            {
                this.btnUpdate.Enabled = false;
            }
        }

        private void TxtPhone_TextChanged(object sender, EventArgs e)
        {
            if (WatchUpdate())
            {
                this.btnUpdate.Enabled = true;
            }
            else
            {
                this.btnUpdate.Enabled = false;
            }
        }

        private void TxtEmail_TextChanged(object sender, EventArgs e)
        {
            if (WatchUpdate())
            {
                this.btnUpdate.Enabled = true;
            }
            else
            {
                this.btnUpdate.Enabled = false;
            }
        }

        private void btnUpdate_Click(object sender, EventArgs e)
        {
            User user1 = new User();
            user1.Email = TxtEmail.Text;
            user1.NickName = TxtNickName.Text;
            user1.PassWord = TxtPassWord.Text;
            user1.Phone = TxtPhone.Text;

            try
            {
                UserDataService.UpdateUserById(GlobalUser.Id, user1);
                MessageBox.Show("更新成功");
            }
            catch (Exception)
            {
                throw;
            }
        }

        private void btnUserManage_Click(object sender, EventArgs e)
        {
            FrmUserManager frm = new FrmUserManager();
            frm.ShowDialog();
        }
    }
}
