package test.junit;

import dao.TeammemDaoImpl;
import dao.TeammenDAO;
import dao.UserDAO;
import dao.UserDaoImpl;
import model.TpExpensebill;
import model.TpTeammems;
import model.TpUser;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.*;

public class TeammemDaoImplTest {
    private TeammenDAO tdao = null;

    @Before
    public void init(){
        tdao = new TeammemDaoImpl();
    }
    @Test
    public void addTeammen() {
            TpTeammems tm = new TpTeammems();
            tm.setId(12);
            tm.setProjectid(12);
            tm.setTeammemberid(25);  // 这个值必须在 tp_user 表中存在
            tm.setMembertype("普通成员");
            System.out.println(tdao.addTeammen(tm));

    }

    @Test
    public void modidyTpExpensebill() {
        // 创建测试数据
        TpExpensebill bill = new TpExpensebill();

        bill.setBillid(12);
        bill.setProjectid(12);        // 确保这个项目ID在tp_table中存在
        bill.setExpensetype("餐饮");
        bill.setPrice("199.99");
        bill.setDescription("团队聚餐");

        bill.setExpensetime("2024-02-02 09:00:00");
        bill.setInvolvedpersons("张三,李四,王五");

        // 执行修改操作
        boolean result = tdao.modidyTpExpensebill(bill);

        // 验证结果
        assertTrue("修改账单信息应该成功", result);

        // 可以进一步验证修改后的数据
        // TpExpensebill updatedBill = tdao.getBillById(1);
        // assertEquals("餐饮", updatedBill.getExpensetype());
        // assertEquals(199.99, updatedBill.getPrice(), 0.01);
    }

    @Test
    public void removeTeammen() {
        System.out.println(tdao.removeTeammem(5));
    }

    @Test
    public void getTeammemById() {
        System.out.println(tdao.getTeammemById(5));
    }

    @Test
    public void getTeammemById2() {
        System.out.println(tdao.getTeammemById2(5));
    }
}