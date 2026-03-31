<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.*" %>
<%@ page import="model.*" %>

<%
    request.setCharacterEncoding("UTF-8");

    try {
        // 获取表单数据
        int projectId = Integer.parseInt(request.getParameter("projectid"));
        int teammemberId = Integer.parseInt(request.getParameter("teammemberid"));
        String memberType = request.getParameter("membertype");
        String creationTime = request.getParameter("creationtime");

        // 创建团队成员对象
        TpTeammems member = new TpTeammems();
        member.setProjectid(projectId);
        member.setTeammemberid(teammemberId);
        member.setMembertype(memberType);
        member.setCreationtime(creationTime);

        // 保存到数据库
        TeammenDAO teamDAO = new TeammemDaoImpl();
        int result = teamDAO.addTeammen(member);

        if (result > 0) {
            // 添加成功，重定向回添加页面
            response.sendRedirect("add-team.jsp?id=" + projectId + "&success=true");
        } else {
            // 添加失败
            response.sendRedirect("add-team.jsp?id=" + projectId + "&error=添加失败");
        }
    } catch (Exception e) {
        e.printStackTrace();
        String projectId = request.getParameter("projectid");
        response.sendRedirect("add-team.jsp?id=" + projectId + "&error=" + e.getMessage());
    }
%>