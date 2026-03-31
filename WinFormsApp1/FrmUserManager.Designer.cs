namespace WinFormsApp1
{
    partial class FrmUserManager
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
            listBox1 = new ListBox();
            button1 = new Button();
            button2 = new Button();
            button3 = new Button();
            button4 = new Button();
            textBox1 = new TextBox();
            button5 = new Button();
            SuspendLayout();
            // 
            // listBox1
            // 
            listBox1.FormattingEnabled = true;
            listBox1.ItemHeight = 24;
            listBox1.Location = new Point(59, 12);
            listBox1.Name = "listBox1";
            listBox1.Size = new Size(1114, 484);
            listBox1.TabIndex = 0;
            // 
            // button1
            // 
            button1.Location = new Point(61, 631);
            button1.Name = "button1";
            button1.Size = new Size(148, 59);
            button1.TabIndex = 1;
            button1.Text = "添加数据";
            button1.UseVisualStyleBackColor = true;
            // 
            // button2
            // 
            button2.Location = new Point(388, 631);
            button2.Name = "button2";
            button2.Size = new Size(148, 59);
            button2.TabIndex = 2;
            button2.Text = "删除数据";
            button2.UseVisualStyleBackColor = true;
            button2.Click += button2_Click;
            // 
            // button3
            // 
            button3.Location = new Point(707, 631);
            button3.Name = "button3";
            button3.Size = new Size(148, 59);
            button3.TabIndex = 3;
            button3.Text = "修改数据";
            button3.UseVisualStyleBackColor = true;
            // 
            // button4
            // 
            button4.Location = new Point(1025, 536);
            button4.Name = "button4";
            button4.Size = new Size(148, 59);
            button4.TabIndex = 4;
            button4.Text = "查询数据";
            button4.UseVisualStyleBackColor = true;
            // 
            // textBox1
            // 
            textBox1.Location = new Point(59, 536);
            textBox1.Multiline = true;
            textBox1.Name = "textBox1";
            textBox1.Size = new Size(956, 58);
            textBox1.TabIndex = 5;
            // 
            // button5
            // 
            button5.Location = new Point(1025, 631);
            button5.Name = "button5";
            button5.Size = new Size(148, 59);
            button5.TabIndex = 6;
            button5.Text = "退出";
            button5.UseVisualStyleBackColor = true;
            button5.Click += button5_Click;
            // 
            // FrmUserManager
            // 
            AutoScaleDimensions = new SizeF(11F, 24F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1261, 717);
            Controls.Add(button5);
            Controls.Add(textBox1);
            Controls.Add(button4);
            Controls.Add(button3);
            Controls.Add(button2);
            Controls.Add(button1);
            Controls.Add(listBox1);
            Name = "FrmUserManager";
            Text = "FrmUserManager";
            Load += FrmUserManager_Load;
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private ListBox listBox1;
        private Button button1;
        private Button button2;
        private Button button3;
        private Button button4;
        private TextBox textBox1;
        private Button button5;
    }
}