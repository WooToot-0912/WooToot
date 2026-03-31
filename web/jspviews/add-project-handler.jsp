<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.TableDAO" %>
<%@ page import="dao.TableDaoImpl" %>
<%@ page import="model.TpTable" %>

<%
    // 设置请求编码
    request.setCharacterEncoding("UTF-8");

    try {
        // 获取表单数据
        int projectId = Integer.parseInt(request.getParameter("projectid"));
        String projectName = request.getParameter("projectname");
        String year = request.getParameter("year");
        String location = request.getParameter("location");
        String startDate = request.getParameter("startdate");
        String endDate = request.getParameter("enddate");
        String status = request.getParameter("status");
        String notes = request.getParameter("notes");

        // 创建项目对象
        TpTable project = new TpTable();
        project.setProjectid(projectId);
        project.setProjectname(projectName);
        project.setYear(year);
        project.setLocation(location);
        project.setStartdate(startDate);
        project.setEnddate(endDate);
        project.setStatus(status);
        project.setNotes(notes);

        // 调用DAO添加项目
        TableDAO tableDAO = new TableDaoImpl();
        int result = tableDAO.addTable(project);

        if (result > 0) {
            // 添加成功，重定向到项目列表页
            response.sendRedirect("index.jsp?success=true");
        } else {
            // 添加失败，返回添加页面并显示错误信息
            response.sendRedirect("edit-project.jsp?error=true");
        }

    } catch (Exception e) {
        e.printStackTrace();
        response.sendRedirect("edit-project.jsp?error=" + e.getMessage());
    }
%>