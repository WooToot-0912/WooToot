package controller;

import dao.UserDAO;
import dao.UserDaoImpl;
import model.TpUser;
import utils.DispatcherUtils;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

@WebServlet("/jspviews/register.do")
public class RegisterServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        try {
            // 1. 获取表单数据并打印日志
            String userid = request.getParameter("username");
            String pwd = request.getParameter("password");
            String confirmPwd = request.getParameter("confirmPassword");

            System.out.println("=== 注册请求开始 ===");
            System.out.println("用户ID: " + userid);
            System.out.println("密码长度: " + (pwd != null ? pwd.length() : 0));

            // 2. 数据验证
            if(userid == null || userid.trim().equals("")) {
                System.out.println("错误：用户账号为空");
                DispatcherUtils.openErrWeb("用户账号不能为空", "register.jsp", request, response);
                return;
            }
            if(pwd == null || pwd.trim().equals("")) {
                System.out.println("错误：密码为空");
                DispatcherUtils.openErrWeb("密码不能为空", "register.jsp", request, response);
                return;
            }
            if(!pwd.equals(confirmPwd)) {
                System.out.println("错误：密码不匹配");
                DispatcherUtils.openErrWeb("两次输入的密码不一致", "register.jsp", request, response);
                return;
            }

            // 3. 创建UserDAO实例
            UserDAO userDao = new UserDaoImpl();

            // 4. 检查用户ID是否已存在
            System.out.println("检查用户ID是否可用...");
            boolean isValid = userDao.isUseridValid(userid);
            System.out.println("用户ID是否可用: " + isValid);

            if(!isValid) {
                System.out.println("错误：用户ID已存在");
                DispatcherUtils.openErrWeb("该用户账号已被注册", "register.jsp", request, response);
                return;
            }

            // 5. 创建新用户对象
            TpUser newUser = new TpUser();
            try {
                int userIdInt = Integer.parseInt(userid);
                newUser.setUserid(userIdInt);
                newUser.setPwd(pwd);
                newUser.setUsertype("管理员");
                newUser.setEmail("");
                newUser.setContactnumber("");

                System.out.println("准备注册用户:");
                System.out.println("UserID: " + newUser.getUserid());
                System.out.println("UserType: " + newUser.getUsertype());

                // 6. 注册用户
                boolean result = userDao.registerUser(newUser);
                System.out.println("注册结果: " + result);

                if(result) {
                    System.out.println("注册成功，跳转到登录页面");
                    response.sendRedirect("login.jsp");
                } else {
                    System.out.println("注册失败");
                    DispatcherUtils.openErrWeb("注册失败，请稍后重试", "register.jsp", request, response);
                }
            } catch (NumberFormatException e) {
                System.out.println("错误：用户ID格式不正确");
                System.out.println("异常信息: " + e.getMessage());
                DispatcherUtils.openErrWeb("用户ID必须是数字", "register.jsp", request, response);
            } catch (Exception e) {
                System.out.println("注册过程发生异常");
                e.printStackTrace();
                DispatcherUtils.openErrWeb("注册失败: " + e.getMessage(), "register.jsp", request, response);
            }

        } catch (Exception e) {
            System.out.println("系统错误");
            e.printStackTrace();
            DispatcherUtils.openErrWeb("系统错误，请稍后重试", "register.jsp", request, response);
        } finally {
            System.out.println("=== 注册请求结束 ===");
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}