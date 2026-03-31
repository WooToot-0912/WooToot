<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.*" %>
<%@ page import="model.*" %>
<%@ page import="java.util.List" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>

<%
    try {
        // 获取项目ID
        String projectIdStr = request.getParameter("id");
        if (projectIdStr == null || projectIdStr.trim().isEmpty()) {
            throw new IllegalArgumentException("项目ID不能为空");
        }

        int projectId = Integer.parseInt(projectIdStr);

        // 获取项目信息
        TableDAO tableDAO = new TableDaoImpl();
        TpTable project = tableDAO.getTableById(projectId);

        if (project == null) {
            throw new IllegalArgumentException("未找到指定项目");
        }

        // 获取该项目的所有消费记录
        ExpensebillDAO billDAO = new ExpensebillDaoImpl();
        List<TpExpensebill> bills = billDAO.getProjectByTeammem(projectId);

        request.setAttribute("project", project);
        request.setAttribute("bills", bills);
    } catch (Exception e) {
        // 记录错误
        e.printStackTrace();
        // 重定向到错误页面或项目列表页面
        response.sendRedirect("edit-project.jsp?error=" + e.getMessage());
        return;
    }
%>

<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>添加消费记录</title>
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="../fonts/fontawesome-free-6.4.0-web/css/all.min.css">
    <link rel="stylesheet" href="../css/add-expense.css">
</head>
<body>
<%@ include file="nav.jsp" %>

<div class="main-content">
    <div class="container">
        <div class="page-header">
            <h2><i class="fa fa-plus-circle"></i> 添加消费记录</h2>
            <p class="subtitle">为 ${project.projectname} 添加新的消费记录</p>
        </div>

        <!-- 添加消费记录表单 -->
        <div class="expense-form">
            <form action="add-expense-handler.jsp" method="post" id="expenseForm">
                <input type="hidden" name="projectid" value="${project.projectid}">

                <div class="form-group">
                    <label for="expensetype"><i class="fa fa-tag"></i> 消费类型</label>
                    <select id="expensetype" name="expensetype" required class="form-control">
                        <option value="">请选择消费类型</option>
                        <option value="交通">交通</option>
                        <option value="住宿">住宿</option>
                        <option value="餐饮">餐饮</option>
                        <option value="门票">门票</option>
                        <option value="购物">购物</option>
                        <option value="其他">其他</option>
                    </select>
                </div>

                <div class="form-group">
                    <label for="price"><i class="fa fa-money-bill"></i> 消费金额</label>
                    <div class="price-input">
                        <span class="currency">¥</span>
                        <input type="number" id="price" name="price" required class="form-control"
                               step="0.01" min="0" placeholder="请输入消费金额">
                    </div>
                </div>

                <div class="form-group">
                    <label for="expensetime"><i class="fa fa-clock"></i> 消费时间</label>
                    <input type="datetime-local" id="expensetime" name="expensetime"
                           required class="form-control">
                </div>

                <div class="form-group">
                    <label for="description"><i class="fa fa-file-alt"></i> 消费描述</label>
                    <textarea id="description" name="description" class="form-control"
                              placeholder="请输入消费详情描述"></textarea>
                </div>

                <div class="form-group">
                    <label for="involvedpersons"><i class="fa fa-users"></i> 涉及人员</label>
                    <input type="text" id="involvedpersons" name="involvedpersons"
                           class="form-control" placeholder="请输入涉及人员，多个人用逗号分隔">
                </div>

                <div class="form-actions">
                    <button type="submit" class="btn-submit">
                        <i class="fa fa-save"></i> 保存记录
                    </button>
                    <button type="button" class="btn-cancel" onclick="history.back()">
                        <i class="fa fa-times"></i> 取消
                    </button>
                </div>
            </form>
        </div>

        <!-- 显示现有消费记录 -->
        <div class="expense-list">
            <h3><i class="fa fa-list"></i> 消费记录列表</h3>
            <div class="table-responsive">
                <table>
                    <thead>
                    <tr>
                        <th>消费类型</th>
                        <th>金额</th>
                        <th>时间</th>
                        <th>描述</th>
                        <th>涉及人员</th>
                        <th>操作</th>
                    </tr>
                    </thead>
                    <tbody>
                    <c:forEach items="${bills}" var="bill">
                        <tr>
                            <td>
                                    <span class="type-badge type-${bill.expensetype}">
                                        <i class="fa fa-tag"></i> ${bill.expensetype}
                                    </span>
                            </td>
                            <td class="amount">
                                ¥<fmt:formatNumber value="${bill.price}" pattern="#,##0.00"/>
                            </td>
                            <td>${bill.expensetime}</td>
                            <td>${bill.description}</td>
                            <td>
                                <div class="member-list">
                                    <c:forEach items="${bill.involvedpersons.split(',')}" var="person">
                                        <span class="member-tag">${person}</span>
                                    </c:forEach>
                                </div>
                            </td>
                            <td class="action-buttons">
                                <a href="edit-expense.jsp?id=${bill.billid}" class="btn-action" title="编辑">
                                    <i class="fa fa-edit"></i>
                                </a>
                                <a href="javascript:void(0)"
                                   onclick="deleteBill(${bill.billid})"
                                   class="btn-action"
                                   title="删除">
                                    <i class="fa fa-trash"></i>
                                </a>
                            </td>
                        </tr>
                    </c:forEach>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    function deleteBill(billId) {
        if (confirm('确定要删除这条消费记录吗？')) {
            window.location.href = 'delete-expense.jsp?id=' + billId;
        }
    }

    // 显示成功或错误消息
    <% if (request.getParameter("success") != null) { %>
    alert("消费记录添加成功！");
    <% } %>
    <% if (request.getParameter("error") != null) { %>
    alert("错误：<%= request.getParameter("error") %>");
    <% } %>
</script>
</body>
</html>