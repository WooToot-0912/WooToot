package controller;

import dao.TeammenDAO;
import dao.TeammemDaoImpl;
import model.TpTeammems;
import utils.DispatcherUtils;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

/**
 * 实现团队成员管理的动作请求控制器
 */
@WebServlet(name = "TeamServlet", value = "/jspviews/team.do")
public class TeamServlet extends HttpServlet {
    private TeammenDAO teamDAO;

    @Override
    public void init() throws ServletException {
        teamDAO = new TeammemDaoImpl();
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 设置请求编码
        request.setCharacterEncoding("UTF-8");

        // 获取操作类型
        String action = request.getParameter("action");

        if (action == null) {
            listTeamMembers(request, response);
            return;
        }

        switch (action) {
            case "add":
                addTeamMember(request, response);
                break;
            case "delete":
                deleteTeamMember(request, response);
                break;
            default:
                listTeamMembers(request, response);
        }
    }

    private void addTeamMember(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 获取表单数据
        String projectIdStr = request.getParameter("projectid");
        String teammemberIdStr = request.getParameter("teammemberid");
        String memberType = request.getParameter("membertype");
        String creationTime = request.getParameter("creationtime");

        // 数据校验
        if (projectIdStr == null || projectIdStr.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("项目ID不能为空", "add-team.jsp", request, response);
            return;
        }
        if (teammemberIdStr == null || teammemberIdStr.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("成员ID不能为空", "add-team.jsp", request, response);
            return;
        }
        if (memberType == null || memberType.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("成员类型不能为空", "add-team.jsp", request, response);
            return;
        }

        try {
            // 转换ID
            int projectId = Integer.parseInt(projectIdStr);
            int teammemberId = Integer.parseInt(teammemberIdStr);

            // 创建团队成员对象
            TpTeammems member = new TpTeammems();
            member.setProjectid(projectId);
            member.setTeammemberid(teammemberId);
            member.setMembertype(memberType);
            member.setCreationtime(creationTime);

            // 调用DAO保存成员
            int result = teamDAO.addTeammen(member);

            if (result > 0) {
                DispatcherUtils.openSuccessWeb("添加团队成员成功",
                        "add-team.jsp?id=" + projectId, request, response);
            } else {
                DispatcherUtils.openErrWeb("添加团队成员失败",
                        "add-team.jsp?id=" + projectId, request, response);
            }
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-team.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-team.jsp", request, response);
        }
    }

    private void deleteTeamMember(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String teammemberIdStr = request.getParameter("id");
        String projectIdStr = request.getParameter("projectid");

        if (teammemberIdStr == null || teammemberIdStr.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("成员ID不能为空", "add-team.jsp", request, response);
            return;
        }

        try {
            int teammemberId = Integer.parseInt(teammemberIdStr);
            boolean result = teamDAO.removeTeammem(teammemberId);

            if (result) {
                String redirectUrl = "add-team.jsp";
                if (projectIdStr != null && !projectIdStr.trim().isEmpty()) {
                    redirectUrl += "?id=" + projectIdStr;
                }
                DispatcherUtils.openSuccessWeb("删除团队成员成功", redirectUrl, request, response);
            } else {
                DispatcherUtils.openErrWeb("删除团队成员失败", "add-team.jsp", request, response);
            }
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-team.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-team.jsp", request, response);
        }
    }

    private void listTeamMembers(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String projectIdStr = request.getParameter("id");

        try {
            if (projectIdStr != null && !projectIdStr.trim().isEmpty()) {
                int projectId = Integer.parseInt(projectIdStr);
                TpTeammems member = teamDAO.getTeammemById2(projectId);
                request.setAttribute("teamMembers", member);
            } else {
                List<TpTeammems> members = teamDAO.getAllTeamMembers();
                request.setAttribute("teamMembers", members);
            }
            request.getRequestDispatcher("add-team.jsp").forward(request, response);
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-team.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-team.jsp", request, response);
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}