<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.*" %>
<%@ page import="model.*" %>

<%
    request.setCharacterEncoding("UTF-8");

    try {
        // 获取表单数据
        int projectId = Integer.parseInt(request.getParameter("projectid"));
        String expenseType = request.getParameter("expensetype");
        double price = Double.parseDouble(request.getParameter("price"));
        String expenseTime = request.getParameter("expensetime");
        String description = request.getParameter("description");
        String involvedPersons = request.getParameter("involvedpersons");

        // 创建消费记录对象
        TpExpensebill bill = new TpExpensebill();
        bill.setProjectid(projectId);
        bill.setExpensetype(expenseType);
        bill.setPrice(String.valueOf(price));
        bill.setExpensetime(expenseTime);
        bill.setDescription(description);
        bill.setInvolvedpersons(involvedPersons);

        // 保存到数据库
        ExpensebillDAO billDAO = new ExpensebillDaoImpl();
        int result = billDAO.addBill(bill);

        if (result > 0) {
            // 添加成功，重定向回添加页面
            response.sendRedirect("add-expense.jsp?id=" + projectId + "&success=true");
        } else {
            // 添加失败
            response.sendRedirect("add-expense.jsp?id=" + projectId + "&error=添加失败");
        }
    } catch (Exception e) {
        e.printStackTrace();
        String projectId = request.getParameter("projectid");
        response.sendRedirect("add-expense.jsp?id=" + projectId + "&error=" + e.getMessage());
    }
%>