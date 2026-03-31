package controller;

import dao.TeammenDAO;
import dao.TeammemDaoImpl;
import dao.UserDAO;
import dao.UserDaoImpl;
import model.TpTeammems;
import model.TpUser;
import utils.DispatcherUtils;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;
import java.io.IOException;
import java.sql.Timestamp;

@WebServlet("/jspviews/add-team.do")
public class AddTeamServlet extends HttpServlet {
    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 检查用户是否登录
        HttpSession session = request.getSession();
        if(session.getAttribute("loginuser") == null) {
            response.sendRedirect("login.jsp");
            return;
        }

        // 设置请求编码
        request.setCharacterEncoding("UTF-8");

        try {
            // 获取表单参数
            int projectId = Integer.parseInt(request.getParameter("projectid"));
            int teamMemberId = Integer.parseInt(request.getParameter("teammemberid"));
            String memberType = request.getParameter("membertype");
            String creationTime = request.getParameter("creationtime");

            // 数据验证
            if (projectId <= 0) {
                throw new IllegalArgumentException("项目ID无效");
            }
            if (teamMemberId <= 0) {
                throw new IllegalArgumentException("成员ID无效");
            }
            if (memberType == null || memberType.trim().isEmpty()) {
                throw new IllegalArgumentException("成员类型不能为空");
            }
            // 检查用户是否存在
            UserDAO userDAO = new UserDaoImpl();
            TpUser user = userDAO.getTUserByid(String.valueOf(teamMemberId));
            if (user == null) {
                throw new IllegalArgumentException("该用户ID不存在，请确认后重试");
            }
            // 验证成员类型是否有效
            if (!memberType.equals("团队管理员") && !memberType.equals("普通成员")) {
                throw new IllegalArgumentException("无效的成员类型");
            }
            if (creationTime == null || creationTime.trim().isEmpty()) {
                throw new IllegalArgumentException("加入时间不能为空");
            }

            // 创建团队成员对象
            TpTeammems teamMember = new TpTeammems();
            teamMember.setId(0); // 设置默认ID，数据库会自动生成
            teamMember.setProjectid(projectId);
            teamMember.setTeammemberid(teamMemberId);
            teamMember.setMembertype(memberType);
            // 将字符串时间转换为Timestamp
            teamMember.setCreationtime(String.valueOf(Timestamp.valueOf(creationTime.replace("T", " ") + ":00")));

            // 调用DAO执行添加操作
            TeammenDAO teamDAO = new TeammemDaoImpl();
            int result = teamDAO.addTeammen(teamMember);

            if (result > 0) {
                // 添加成功，重定向回列表页面
                response.sendRedirect("add-team.jsp?success=true");
            } else {
                // 添加失败
                throw new Exception("添加团队成员失败");
            }

        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式无效", "add-team.jsp", request, response);
        } catch (IllegalArgumentException e) {
            DispatcherUtils.openErrWeb(e.getMessage(), "add-team.jsp", request, response);
        } catch (Exception e) {
            e.printStackTrace();
            DispatcherUtils.openErrWeb("添加团队成员时发生错误：" + e.getMessage(),
                    "add-team.jsp", request, response);
        }
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 检查用户是否登录
        HttpSession session = request.getSession();
        if(session.getAttribute("loginuser") == null) {
            response.sendRedirect("login.jsp");
            return;
        }
        // GET请求重定向到添加页面
        response.sendRedirect("add-team.jsp");
    }
}