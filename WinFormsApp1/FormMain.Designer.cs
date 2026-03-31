namespace WinFormsApp1
{
    partial class FormMain
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            TxtUserName = new TextBox();
            TxtPassWord = new TextBox();
            TxtNickName = new TextBox();
            TxtPhone = new TextBox();
            TxtEmail = new TextBox();
            btnUpdate = new Button();
            btnwh = new Button();
            btnUserManage = new Button();
            label1 = new Label();
            label2 = new Label();
            label3 = new Label();
            label4 = new Label();
            label5 = new Label();
            SuspendLayout();
            // 
            // TxtUserName
            // 
            TxtUserName.Location = new Point(429, 228);
            TxtUserName.Name = "TxtUserName";
            TxtUserName.ReadOnly = true;
            TxtUserName.Size = new Size(249, 30);
            TxtUserName.TabIndex = 0;
            // 
            // TxtPassWord
            // 
            TxtPassWord.Location = new Point(429, 335);
            TxtPassWord.Name = "TxtPassWord";
            TxtPassWord.Size = new Size(249, 30);
            TxtPassWord.TabIndex = 1;
            TxtPassWord.TextChanged += TxtPassWord_TextChanged;
            // 
            // TxtNickName
            // 
            TxtNickName.Location = new Point(429, 127);
            TxtNickName.Name = "TxtNickName";
            TxtNickName.Size = new Size(249, 30);
            TxtNickName.TabIndex = 2;
            TxtNickName.TextChanged += TxtNickName_TextChanged;
            // 
            // TxtPhone
            // 
            TxtPhone.Location = new Point(429, 433);
            TxtPhone.Name = "TxtPhone";
            TxtPhone.Size = new Size(249, 30);
            TxtPhone.TabIndex = 3;
            TxtPhone.TextChanged += TxtPhone_TextChanged;
            // 
            // TxtEmail
            // 
            TxtEmail.Location = new Point(429, 539);
            TxtEmail.Name = "TxtEmail";
            TxtEmail.Size = new Size(249, 30);
            TxtEmail.TabIndex = 4;
            TxtEmail.TextChanged += TxtEmail_TextChanged;
            // 
            // btnUpdate
            // 
            btnUpdate.Enabled = false;
            btnUpdate.Font = new Font("Microsoft YaHei UI", 12F, FontStyle.Regular, GraphicsUnit.Point, 134);
            btnUpdate.Location = new Point(481, 630);
            btnUpdate.Name = "btnUpdate";
            btnUpdate.Size = new Size(148, 56);
            btnUpdate.TabIndex = 5;
            btnUpdate.Text = "更新";
            btnUpdate.UseVisualStyleBackColor = true;
            btnUpdate.Click += btnUpdate_Click;
            // 
            // btnwh
            // 
            btnwh.Font = new Font("Microsoft YaHei UI", 12F, FontStyle.Regular, GraphicsUnit.Point, 134);
            btnwh.Location = new Point(130, 724);
            btnwh.Name = "btnwh";
            btnwh.Size = new Size(243, 85);
            btnwh.TabIndex = 6;
            btnwh.Text = "打开温湿度管理页面";
            btnwh.UseVisualStyleBackColor = true;
            // 
            // btnUserManage
            // 
            btnUserManage.Font = new Font("Microsoft YaHei UI", 12F, FontStyle.Regular, GraphicsUnit.Point, 134);
            btnUserManage.Location = new Point(724, 724);
            btnUserManage.Name = "btnUserManage";
            btnUserManage.Size = new Size(243, 85);
            btnUserManage.TabIndex = 7;
            btnUserManage.Text = "用户管理";
            btnUserManage.UseVisualStyleBackColor = true;
            btnUserManage.Click += btnUserManage_Click;
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Location = new Point(293, 133);
            label1.Name = "label1";
            label1.Size = new Size(46, 24);
            label1.TabIndex = 8;
            label1.Text = "匿名";
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Location = new Point(293, 234);
            label2.Name = "label2";
            label2.Size = new Size(46, 24);
            label2.TabIndex = 9;
            label2.Text = "账号";
            // 
            // label3
            // 
            label3.AutoSize = true;
            label3.Location = new Point(293, 341);
            label3.Name = "label3";
            label3.Size = new Size(46, 24);
            label3.TabIndex = 10;
            label3.Text = "密码";
            // 
            // label4
            // 
            label4.AutoSize = true;
            label4.Location = new Point(293, 439);
            label4.Name = "label4";
            label4.Size = new Size(64, 24);
            label4.TabIndex = 11;
            label4.Text = "手机号";
            // 
            // label5
            // 
            label5.AutoSize = true;
            label5.Location = new Point(293, 545);
            label5.Name = "label5";
            label5.Size = new Size(46, 24);
            label5.TabIndex = 12;
            label5.Text = "邮箱";
            // 
            // FormMain
            // 
            AutoScaleDimensions = new SizeF(11F, 24F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1116, 883);
            Controls.Add(label5);
            Controls.Add(label4);
            Controls.Add(label3);
            Controls.Add(label2);
            Controls.Add(label1);
            Controls.Add(btnUserManage);
            Controls.Add(btnwh);
            Controls.Add(btnUpdate);
            Controls.Add(TxtEmail);
            Controls.Add(TxtPhone);
            Controls.Add(TxtNickName);
            Controls.Add(TxtPassWord);
            Controls.Add(TxtUserName);
            Name = "FormMain";
            StartPosition = FormStartPosition.CenterScreen;
            Text = "FormMain";
            Load += FormMain_Load;
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private TextBox TxtUserName;
        private TextBox TxtPassWord;
        private TextBox TxtNickName;
        private TextBox TxtPhone;
        private TextBox TxtEmail;
        private Button btnUpdate;
        private Button btnwh;
        private Button btnUserManage;
        private Label label1;
        private Label label2;
        private Label label3;
        private Label label4;
        private Label label5;
    }
}