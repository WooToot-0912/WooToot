package test.junit;

import model.TpTable;
import org.junit.Before;
import org.junit.Test;
import utils.DataUtil;
import utils.DataUtil1;

import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

public class EntityBeanTest {
    DataUtil1 dataUtil = null;
    @Before
    public void init(){
        dataUtil = new DataUtil();
    }

    @Test
    public void test1(){
        TpTable table = new TpTable();
        table.setProjectid(12);
        table.setProjectname("四川热旅");
        table.setYear("2025");
        table.setLocation("四川");
        table.setStartdate("2025-5-1 00:00:00");
        table.setEnddate("2025-7-1 00:00:00");
        table.setNotes("");
        table.setStatus("计划中");

        System.out.println(table.getProjectid());
        System.out.println(table.getProjectname());
        System.out.println(table.getYear());
        System.out.println(table.getLocation());
        System.out.println(table.getStartdate());
        System.out.println(table.getEnddate());
        System.out.println(table.getNotes());
        System.out.println(table.getStatus());
    }

    @Test
    public void test2()throws Exception {
        TpTable table = new TpTable();

        String sql = "select *from tp_table where projectid = ?";
        Object[] para = {"4"};
        ResultSet rs = dataUtil.select(sql,para);
        if(rs!=null && rs.next()){
            table.setProjectname(rs.getString("projectname"));
            table.setYear(rs.getString("year"));
            table.setLocation(rs.getString("location"));
            table.setStartdate(rs.getString("startdate"));
            table.setEnddate(rs.getString("enddate"));
            table.setNotes(rs.getString("notes"));
            table.setStatus(rs.getString("status"));
        }
        dataUtil.close();

        System.out.println(table.getProjectid());
        System.out.println(table.getProjectname());
        System.out.println(table.getYear());
        System.out.println(table.getLocation());
        System.out.println(table.getStartdate());
        System.out.println(table.getEnddate());
        System.out.println(table.getNotes());
        System.out.println(table.getStatus());
    }

    @Test
    public void test3() throws Exception {
        String sql = "select * from tp_table ";
        ResultSet rs = dataUtil.select(sql,null);
        List<TpTable> list = new ArrayList<TpTable>();

        while(rs!=null && rs.next()) {
            TpTable table = new TpTable();
            table.setProjectid(rs.getInt("projectid"));
            table.setProjectname(rs.getString("projectname"));
            table.setYear(rs.getString("year"));
            table.setLocation(rs.getString("location"));
            table.setStartdate(rs.getString("startdate"));
            table.setEnddate(rs.getString("enddate"));
            table.setNotes(rs.getString("notes"));
            table.setStatus(rs.getString("status"));
            list.add(table);
        }
        dataUtil.close();

        System.out.println(list.size());
        System.out.println(list);
    }

    @Test
    public void test4()throws Exception {
        String sql = "select * from tp_table where projectid = ?";
        Object[] para = {12};
        ResultSet rs = dataUtil.select(sql, para);
        TpTable table = new TpTable();
        dataUtil.close();
        System.out.println(table);
    }

    @Test
    public void test5()throws Exception {
        String sql = "select * from tp_table";
        ResultSet rs = dataUtil.select(sql,null);
        List<TpTable> list = TpTable.tranList(rs);
        dataUtil.close();
        System.out.println(list);
    }
}
