package controller;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.IOException;
import utils.DispatcherUtils;

/**
 * 实现用户管理的动作请求控制器
 */
@WebServlet(name = "UserServlet", value = "/jspviews/user.do")
public class UserServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 设置请求编码
        request.setCharacterEncoding("UTF-8");

        // 获取操作类型
        String action = request.getParameter("action");

        if (action == null) {
            showLoginForm(request, response);
            return;
        }

        switch (action) {
            case "login":
                login(request, response);
                break;
            case "logout":
                logout(request, response);
                break;
            default:
                showLoginForm(request, response);
        }
    }

    private void showLoginForm(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        request.getRequestDispatcher("login.jsp").forward(request, response);
    }

    private void login(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String username = request.getParameter("username");
        String password = request.getParameter("password");

        // 数据校验
        if (username == null || username.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("用户名不能为空", "login.jsp", request, response);
            return;
        }
        if (password == null || password.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("密码不能为空", "login.jsp", request, response);
            return;
        }

        // 这里应该添加实际的用户验证逻辑
        if ("admin".equals(username) && "admin".equals(password)) {
            // 登录成功，创建会话
            HttpSession session = request.getSession();
            session.setAttribute("username", username);
            session.setAttribute("isLoggedIn", true);

            // 重定向到主页
            response.sendRedirect("index.jsp");
        } else {
            DispatcherUtils.openErrWeb("用户名或密码错误", "login.jsp", request, response);
        }
    }

    private void logout(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 获取会话并使其失效
        HttpSession session = request.getSession(false);
        if (session != null) {
            session.invalidate();
        }

        // 重定向到登录页面
        response.sendRedirect("login.jsp");
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}