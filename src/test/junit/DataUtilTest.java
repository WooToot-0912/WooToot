package test.junit;

import org.junit.Before;
import org.junit.Test;
import utils.DataUtil;
import utils.DataUtil1;

import java.sql.ResultSet;

import static org.junit.Assert.*;
public class DataUtilTest {
    private DataUtil1 dataUtil = null;
    @Before
    public void init(){dataUtil = new DataUtil();
    }

    @Test
    public void insert() {
        String sql = "insert into tp_table(projectname,year,status) values(?,?,?)";
        Object[] para ={"云南秘境之旅","2024","计划中"};
        int keyOrRows =dataUtil.insert(sql,para);
        System.out.println("返回值是：" + keyOrRows);
    }

    @Test
    public void update() {
        String sql ="update tp_table set location=?,startdate=?,enddate=?,notes=?";
        Object[]para = {"中国","2024-12-1 00:00:00","2024-1-1 00:00:00","去有风的地方"};
        System.out.println("受影响行数：" + dataUtil.update(sql,para));
    }

    @Test
    public void delete() {
        String sql ="select from tp_table where projectname=?";
        Object[] para = {"云南秘境之旅"};
        System.out.println("受影响行数：" + dataUtil.update(sql,para));
    }

    @Test
    public void select() throws Exception {
        String sql ="select * from tp_table";
        ResultSet rs = dataUtil.select(sql,null);
        while(rs!=null && rs.next()){
            System.out.println(rs.getObject("projectid")+" "+
                    rs.getObject("projectname")+" "+
                    rs.getObject("location"));
        }
        dataUtil.close();
    }

    @Test
    public void selectCount() {
        String sql ="select count(*) from tp_table";
        int amount = dataUtil.selectCount(sql,null);
        System.out.println("总共有项目"+amount+"个");
    }

    @Test
    public void callProcedureWithQuery() throws Exception {
        ResultSet rs = dataUtil.callProcedureWithQuery("up_getsystime()",null);
        while(rs!=null &&  rs.next()){
            System.out.println(rs.getObject(11));
        }
        dataUtil.close();
    }
}