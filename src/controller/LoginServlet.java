package controller;

import dao.UserDAO;
import dao.UserDaoImpl;
import model.TpUser;
import utils.DispatcherUtils;

import javax.servlet.*;
import javax.servlet.http.*;
import javax.servlet.annotation.*;
import java.io.IOException;

/**
 * 用户登录操作请求控制器
 */
@WebServlet(name = "LoginServlet", value = "/jspviews/login.do")
public class LoginServlet extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        //（1）获取参数
        String userid = request.getParameter("username");
        String pwd = request.getParameter("password");

        //（2）数据校验
        if(userid == null || userid.equals("")){
            DispatcherUtils.openErrWeb("登录用户账号不能为空","login.jsp",request,response);
            return;
        }else if(pwd == null || pwd.equals("")){
            DispatcherUtils.openErrWeb("登录用户密码不能为空","login.jsp",request,response);
            return;
        }

        //（3）身份验证
        UserDAO udao = new UserDaoImpl();
        TpUser loginuser = udao.login(userid, pwd);

        //（4）页面跳转
        if(loginuser != null && loginuser.getUserid() > 0){
            HttpSession session = request.getSession();
            session.setAttribute("loginuser", loginuser);
            // 确保路径正确
            response.sendRedirect("index.do"); // 相对路径
            // 或者使用绝对路径
            // response.sendRedirect(request.getContextPath() + "/jspviews/index.do");
        }else{
            DispatcherUtils.openErrWeb("您输入的用户账号和密码不正确","login.jsp",request,response);
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}