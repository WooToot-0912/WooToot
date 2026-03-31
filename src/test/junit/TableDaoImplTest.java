package test.junit;

import dao.TableDAO;
import dao.TableDaoImpl;
import model.TpTable;
import org.junit.Before;
import org.junit.Test;

import static org.junit.Assert.*;

public class TableDaoImplTest {
    private TableDAO tdao = null;

    @Before
    public  void init(){
        tdao = new TableDaoImpl();
    }

    @Test
    public void addTable() {
        TpTable table = new TpTable();
        table.setProjectid(12);
        table.setProjectname("云南秘境之旅");
        table.setYear("2025");
        table.setStatus("计划中");
        System.out.println(tdao.addTable(table));
    }

    @Test
    public void modifyTable() {
        TpTable table = tdao.getTableById(3);
        table.setLocation("日本");
        //table.setNotes("去有风的地方");
        System.out.println(tdao.modifyTable(table));
    }

    @Test
    public void removeTable() {
        // 先确保数据库中有 projectid=11 的记录
        TpTable existingTable = tdao.getTableById(12);
        if (existingTable != null) {
            boolean result = tdao.removeTable(12);
            assertTrue("删除操作应该成功", result);

            // 验证记录确实被删除
            assertNull("记录应该已被删除", tdao.getTableById(12));
        } else {
            System.out.println("测试数据不存在，请先添加测试数据");
        }
    }

    @Test
    public void getTableById() {
        System.out.println(tdao.getTableById(1));
    }

    @Test
    public void getTableByName(){
        System.out.println(tdao.getTableByName("云南秘境之旅"));
    }

    @Test
    public void getTablesByUser() {
        System.out.println(tdao.getTablesByUser(5));
        System.out.println(tdao.getTablesByUser(1));
    }

    @Test
    public void getTableByProjectnameAndYear() {
        System.out.println(tdao.getTableByProjectnameAndYear(null,null));
    }



}