package controller;

import dao.ExpensebillDAO;
import dao.ExpensebillDaoImpl;
import model.TpExpensebill;
import utils.DispatcherUtils;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;

/**
 * 实现消费账单管理的动作请求控制器
 */
@WebServlet(name = "ExpenseServlet", value = "/jspviews/expense.do")
public class ExpenseServlet extends HttpServlet {
    private ExpensebillDAO expenseDAO;

    @Override
    public void init() throws ServletException {
        expenseDAO = new ExpensebillDaoImpl();
    }

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 设置请求编码
        request.setCharacterEncoding("UTF-8");

        // 获取操作类型
        String action = request.getParameter("action");

        if (action == null) {
            listExpenses(request, response);
            return;
        }

        switch (action) {
            case "add":
                addExpense(request, response);
                break;
            case "edit":
                editExpense(request, response);
                break;
            case "delete":
                deleteExpense(request, response);
                break;
            case "view":
                viewExpense(request, response);
                break;
            default:
                listExpenses(request, response);
        }
    }

    private void addExpense(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 获取表单数据
        String projectIdStr = request.getParameter("projectid");
        String expenseType = request.getParameter("expensetype");
        String price = request.getParameter("price");
        String description = request.getParameter("description");
        String expenseTime = request.getParameter("expensetime");
        String involvedPersons = request.getParameter("involvedpersons");

        // 数据校验
        if (projectIdStr == null || projectIdStr.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("项目ID不能为空", "add-expense.jsp", request, response);
            return;
        }
        if (expenseType == null || expenseType.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("消费类型不能为空", "add-expense.jsp", request, response);
            return;
        }
        if (price == null || price.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("消费金额不能为空", "add-expense.jsp", request, response);
            return;
        }

        try {
            // 转换ID
            int projectId = Integer.parseInt(projectIdStr);

            // 创建消费记录对象
            TpExpensebill bill = new TpExpensebill();
            bill.setProjectid(projectId);
            bill.setExpensetype(expenseType);
            bill.setPrice(price);
            bill.setDescription(description);
            bill.setExpensetime(expenseTime);
            bill.setInvolvedpersons(involvedPersons);

            // 调用DAO保存消费记录
            int result = expenseDAO.addBill(bill);

            if (result > 0) {
                DispatcherUtils.openSuccessWeb("添加消费记录成功",
                        "add-expense.jsp?id=" + projectId, request, response);
            } else {
                DispatcherUtils.openErrWeb("添加消费记录失败",
                        "add-expense.jsp?id=" + projectId, request, response);
            }
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-expense.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-expense.jsp", request, response);
        }
    }

    private void editExpense(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        // 获取表单数据
        String billIdStr = request.getParameter("billid");
        String projectIdStr = request.getParameter("projectid");
        String expenseType = request.getParameter("expensetype");
        String price = request.getParameter("price");
        String description = request.getParameter("description");
        String expenseTime = request.getParameter("expensetime");
        String involvedPersons = request.getParameter("involvedpersons");

        // 数据校验
        if (billIdStr == null || billIdStr.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("账单ID不能为空", "add-expense.jsp", request, response);
            return;
        }

        try {
            // 转换ID
            int billId = Integer.parseInt(billIdStr);
            int projectId = Integer.parseInt(projectIdStr);

            // 创建消费记录对象
            TpExpensebill bill = new TpExpensebill();
            bill.setBillid(billId);
            bill.setProjectid(projectId);
            bill.setExpensetype(expenseType);
            bill.setPrice(price);
            bill.setDescription(description);
            bill.setExpensetime(expenseTime);
            bill.setInvolvedpersons(involvedPersons);

            // 调用DAO更新消费记录
            boolean result = expenseDAO.modifyBill(bill);

            if (result) {
                DispatcherUtils.openSuccessWeb("更新消费记录成功",
                        "add-expense.jsp?id=" + projectId, request, response);
            } else {
                DispatcherUtils.openErrWeb("更新消费记录失败",
                        "add-expense.jsp?id=" + projectId, request, response);
            }
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-expense.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-expense.jsp", request, response);
        }
    }

    private void deleteExpense(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String billIdStr = request.getParameter("id");
        String projectIdStr = request.getParameter("projectid");

        if (billIdStr == null || billIdStr.trim().isEmpty()) {
            DispatcherUtils.openErrWeb("账单ID不能为空", "add-expense.jsp", request, response);
            return;
        }

        try {
            int billId = Integer.parseInt(billIdStr);
            boolean result = expenseDAO.removeBill(billId);

            if (result) {
                String redirectUrl = "add-expense.jsp";
                if (projectIdStr != null && !projectIdStr.trim().isEmpty()) {
                    redirectUrl += "?id=" + projectIdStr;
                }
                DispatcherUtils.openSuccessWeb("删除消费记录成功", redirectUrl, request, response);
            } else {
                DispatcherUtils.openErrWeb("删除消费记录失败", "add-expense.jsp", request, response);
            }
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-expense.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-expense.jsp", request, response);
        }
    }

    private void viewExpense(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String billIdStr = request.getParameter("id");

        try {
            int billId = Integer.parseInt(billIdStr);
            TpExpensebill bill = expenseDAO.getBillById(billId);

            if (bill != null) {
                request.setAttribute("bill", bill);
                request.getRequestDispatcher("view-bill.jsp").forward(request, response);
            } else {
                DispatcherUtils.openErrWeb("消费记录不存在", "add-expense.jsp", request, response);
            }
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-expense.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-expense.jsp", request, response);
        }
    }

    private void listExpenses(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String projectIdStr = request.getParameter("id");

        try {
            List<TpExpensebill> bills;
            if (projectIdStr != null && !projectIdStr.trim().isEmpty()) {
                int projectId = Integer.parseInt(projectIdStr);
                bills = expenseDAO.getProjectByTeammem(projectId);
            } else {
                bills = expenseDAO.getAllBills();
            }
            request.setAttribute("bills", bills);
            request.getRequestDispatcher("view-bill.jsp").forward(request, response);
        } catch (NumberFormatException e) {
            DispatcherUtils.openErrWeb("ID格式不正确", "add-expense.jsp", request, response);
        } catch (Exception e) {
            DispatcherUtils.openErrWeb("系统错误：" + e.getMessage(),
                    "add-expense.jsp", request, response);
        }
    }

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        doGet(request, response);
    }
}