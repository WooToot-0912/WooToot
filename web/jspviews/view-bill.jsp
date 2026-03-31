<%@ page contentType="text/html;charset=UTF-8" language="java" %>
<%@ page import="dao.*" %>
<%@ page import="model.*" %>
<%@ page import="java.util.List" %>
<%@ page import="java.sql.ResultSet" %>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fmt" uri="http://java.sun.com/jsp/jstl/fmt" %>

<%
    try {
        ExpensebillDAO billDAO = new ExpensebillDaoImpl();
        TableDAO tableDAO = new TableDaoImpl();
        List<TpExpensebill> bills = null;
        TpTable project = null;

        // 获取项目ID参数
        String projectIdStr = request.getParameter("id");

        if (projectIdStr != null && !projectIdStr.trim().isEmpty()) {
            // 如果有项目ID，显示特定项目的账单
            int projectId = Integer.parseInt(projectIdStr);
            project = tableDAO.getTableById(projectId);
            bills = billDAO.getProjectByTeammem(projectId);

            request.setAttribute("project", project);
        } else {
            // 如果没有项目ID，显示所有账单
            bills = billDAO.getAllBills();
        }

        // 计算总金额和人均金额
        double totalAmount = 0;
        if (bills != null) {
            for (TpExpensebill bill : bills) {
                try {
                    totalAmount += Double.parseDouble(bill.getPrice());
                } catch (NumberFormatException e) {
                    // 忽略无效的价格格式
                }
            }
        }

        int billCount = bills != null ? bills.size() : 0;
        double averageAmount = billCount > 0 ? totalAmount / 15 : 0; // 假设15人

        request.setAttribute("bills", bills);
        request.setAttribute("totalAmount", totalAmount);
        request.setAttribute("billCount", billCount);
        request.setAttribute("averageAmount", averageAmount);

    } catch (Exception e) {
        e.printStackTrace();
        response.sendRedirect("edit-project.jsp?error=" + e.getMessage());
        return;
    }
%>

<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>查看账单</title>
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="../fonts/fontawesome-free-6.4.0-web/css/all.min.css">
    <link rel="stylesheet" href="../css/view-bill.css">
</head>
<body>
<%@ include file="nav.jsp" %>

<div class="main-content">
    <div class="container">
        <div class="page-header">
            <h2><i class="fa fa-file-invoice-dollar"></i> 旅游账单</h2>
            <c:choose>
                <c:when test="${project != null}">
                    <p class="subtitle">查看 ${project.projectname} 的账单信息</p>
                </c:when>
                <c:otherwise>
                    <p class="subtitle">查看所有项目账单信息</p>
                </c:otherwise>
            </c:choose>
        </div>

        <!-- 账单概览 -->
        <div class="bill-summary">
            <div class="summary-header">
                <h3><i class="fa fa-info-circle"></i> 账单概览</h3>
                <div class="summary-actions">
                    <button class="btn-export" onclick="exportBill()">
                        <i class="fa fa-download"></i> 导出账单
                    </button>
                    <button class="btn-print" onclick="printBill()">
                        <i class="fa fa-print"></i> 打印
                    </button>
                </div>
            </div>
            <div class="summary-content">
                <c:if test="${project != null}">
                    <div class="summary-item">
                        <span class="item-label"><i class="fa fa-bookmark"></i> 项目名称</span>
                        <span class="item-value">${project.projectname}</span>
                    </div>
                    <div class="summary-item">
                        <span class="item-label"><i class="fa fa-calendar"></i> 项目周期</span>
                        <span class="item-value">${project.startdate} 至 ${project.enddate}</span>
                    </div>
                </c:if>
                <div class="summary-stats">
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fa fa-money-bill-wave"></i>
                        </div>
                        <div class="stat-info">
                            <span class="stat-label">总支出</span>
                            <span class="stat-value">¥<fmt:formatNumber value="${totalAmount}" pattern="#,##0.00"/></span>
                        </div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-icon">
                            <i class="fa fa-receipt"></i>
                        </div>
                        <div class="stat-info">
                            <span class="stat-label">消费笔数</span>
                            <span class="stat-value">${billCount}笔</span>
                        </div>
                    </div>
                    <c:if test="${project != null}">
                        <div class="stat-card">
                            <div class="stat-icon">
                                <i class="fa fa-user"></i>
                            </div>
                            <div class="stat-info">
                                <span class="stat-label">人均支出</span>
                                <span class="stat-value">¥<fmt:formatNumber value="${averageAmount}" pattern="#,##0.00"/></span>
                            </div>
                        </div>
                    </c:if>
                </div>
            </div>
        </div>

        <!-- 账单列表 -->
        <div class="bill-list">
            <div class="list-header">
                <h3><i class="fa fa-list"></i> 消费明细</h3>
                <div class="list-filter">
                    <select class="form-control" id="typeFilter" onchange="filterBills()">
                        <option value="">全部类型</option>
                        <option value="交通">交通</option>
                        <option value="住宿">住宿</option>
                        <option value="餐饮">餐饮</option>
                        <option value="门票">门票</option>
                    </select>
                    <div class="date-range">
                        <input type="date" class="form-control" id="startDate" onchange="filterBills()">
                        <span class="date-separator">至</span>
                        <input type="date" class="form-control" id="endDate" onchange="filterBills()">
                    </div>
                </div>
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                    <tr>
                        <c:if test="${project == null}">
                            <th>项目名称</th>
                        </c:if>
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
                            <c:if test="${project == null}">
                                <td>${bill.projectname}</td>
                            </c:if>
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
                                <a href="view-bill.jsp?id=${bill.billid}" class="btn-action" title="编辑">
                                    <i class="fa fa-edit"></i>
                                </a>
                                <a href="javascript:void(0)" onclick="deleteBill(${bill.billid})"
                                   class="btn-action" title="删除">
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

<script src="../js/jquery-3.6.0.min.js"></script>
<script>
    // 查看账单详情
    function viewBill(billId) {
        // 实现查看详情的逻辑
        alert('查看账单详情：' + billId);
    }

    // 删除账单
    function deleteBill(billId) {
        if (confirm('确定要删除这条账单记录吗？')) {
            // 实现删除逻辑
            window.location.href = 'delete-bill.jsp?id=' + billId;
        }
    }

    // 导出账单
    function exportBill() {
        // 实现导出逻辑
        alert('导出功能待实现');
    }

    // 打印账单
    function printBill() {
        window.print();
    }

    // 筛选账单
    function filterBills() {
        // 实现筛选逻辑
        const type = document.getElementById('typeFilter').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        // 添加筛选实现
    }

    // 更新图表
    function updateChart() {
        // 实现图表更新逻辑
        const chartType = document.getElementById('chartType').value;
        // 添加图表更新实现
    }
</script>
</body>
</html>
