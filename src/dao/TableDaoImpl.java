package dao;

import model.TpTable;
import utils.DataUtil;
import utils.DataUtil1;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class TableDaoImpl implements TableDAO{
    private DataUtil1 dataUtil = null;

    public TableDaoImpl(){
        dataUtil = new DataUtil();
    }
    @Override
    public int addTable(TpTable record) {
        String sql ="insert into tp_table(projectid,projectname,year,location," +
                "startdate,enddate,notes,status) " +
                "values(?,?,?,?,?,?,?,?)";
        Object[] para ={record.getProjectid(),record.getProjectname(),record.getYear(),
                record.getLocation(),record.getStartdate(),record.getEnddate(),record.getNotes(),record.getStatus()};
        int keys = dataUtil.insert(sql,para);
        return keys;
    }

    @Override
    public boolean modifyTable(TpTable record) {
        // 添加调试输出
        System.out.println("执行修改操作...");
        System.out.println("项目ID: " + record.getProjectid());

        String sql = "UPDATE tp_table SET projectname=?, year=?, location=?, " +
                "startdate=?, enddate=?, notes=?, status=? WHERE projectid=?";

        // 打印所有要更新的值
        System.out.println("更新的值：");
        System.out.println("projectname: " + record.getProjectname());
        System.out.println("year: " + record.getYear());
        System.out.println("location: " + record.getLocation());
        System.out.println("startdate: " + record.getStartdate());
        System.out.println("enddate: " + record.getEnddate());
        System.out.println("notes: " + record.getNotes());
        System.out.println("status: " + record.getStatus());

        Object[] para = {
                record.getProjectname(),
                record.getYear(),
                record.getLocation(),
                record.getStartdate(),
                record.getEnddate(),
                record.getNotes(),
                record.getStatus(),
                record.getProjectid()  // WHERE 条件中的 projectid
        };

        try {
            int rows = dataUtil.update(sql, para);
            System.out.println("SQL语句: " + sql);
            System.out.println("影响行数: " + rows);
            return rows > 0;
        } catch (Exception e) {
            System.out.println("更新失败: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    @Override
    public boolean removeTable(int projectid) {
        String sql = "delete from tp_table where projectid = ?";
        Object[] para = {projectid};

        try {
            int rows = dataUtil.delete(sql, para);
            return rows > 0;
        } catch (Exception e) {
            e.printStackTrace();
            return false;
        }
    }

    /*@Override
    public TpTable getTableById(int projectid) {
        String sql ="select * from tp_table where projectid = ?";
        Object[] para ={projectid};
        ResultSet rs = dataUtil.select(sql,para);
        TpTable table =new TpTable(rs);
        dataUtil.close();
        return table;
    }*/
    @Override
    public TpTable getTableById(int projectid) {
        System.out.println("正在查询项目ID: " + projectid);
        String sql = "select * from tp_table where projectid = ?";
        Object[] para = {projectid};
        ResultSet rs = null;
        TpTable table = null;

        try {
            rs = dataUtil.select(sql, para);
            if (rs != null && rs.next()) {
                table = new TpTable();
                table.setProjectid(rs.getInt("projectid"));
                table.setProjectname(rs.getString("projectname"));
                table.setYear(rs.getString("year"));
                table.setLocation(rs.getString("location"));
                table.setStartdate(rs.getString("startdate"));
                table.setEnddate(rs.getString("enddate"));
                table.setNotes(rs.getString("notes"));
                table.setStatus(rs.getString("status"));
                System.out.println("查询结果: " + table);
            } else {
                System.out.println("未找到ID为 " + projectid + " 的项目");
            }
        } catch (Exception e) {
            System.out.println("查询出错: " + e.getMessage());
            e.printStackTrace();
        } finally {
            dataUtil.close();
        }
        return table;
    }

    @Override
    public TpTable getTableByName(String projectname) {
        String sql ="select * from tp_table where projectname = ?";
        Object[] para ={projectname};
        ResultSet rs = dataUtil.select(sql,para);
        TpTable table = null;
        try {
            table = new TpTable(rs);
        } catch (SQLException e) {
            throw new RuntimeException(e);
        }
        dataUtil.close();
        return table;
    }

    @Override
    public List<TpTable> getTablesByUser(int projectid) {
        String sql ="select * from tp_table where projectid = ?";
        Object[] para ={projectid};
        ResultSet rs = dataUtil.select(sql,para);
        List<TpTable> list = TpTable.tranList(rs);
        dataUtil.close();
        return list;
    }

    @Override
    public List<TpTable> getTableByProjectnameAndYear(String projectname, String year) {
        List<TpTable> list = null;
        if((projectname!=null && !projectname.equals("")) && (year!=null && !year.equals(""))){
            String sql ="select * from tp_table where projectname like ? and year like ?";
            Object[] para ={"%"+projectname+"%","%"+year+"%"};
            ResultSet rs = dataUtil.select(sql,para);
            list = TpTable.tranList(rs);
            dataUtil.close();
        } else if ((projectname!=null && !projectname.equals("")) && (year==null || year.equals(""))) {
            String sql ="select * from tp_table where projectname like ? and year like ?";
            Object[] para ={"%"+projectname+"%"};
            ResultSet rs = dataUtil.select(sql,para);
            list = TpTable.tranList(rs);
            dataUtil.close();
        }else if((projectname==null || projectname.equals("")) && (year!=null && !year.equals(""))){
            String sql ="select * from tp_table where projectname like ? and year like ?";
            Object[] para ={"%"+year+"%"};
            ResultSet rs = dataUtil.select(sql,para);
            list = TpTable.tranList(rs);
            dataUtil.close();
        }else{
            String sql ="select * from tp_table";
            ResultSet rs = dataUtil.select(sql,null);
            list = TpTable.tranList(rs);
            dataUtil.close();
        }

        return list;
    }
    // 添加新的多条件搜索方法
    @Override
    public List<TpTable> searchProjects(String projectname, String status, String year, String location) {
        List<TpTable> list = new ArrayList<>();
        List<Object> params = new ArrayList<>();

        StringBuilder sql = new StringBuilder("SELECT * FROM tp_table WHERE 1=1");

        // 项目名称模糊查询
        if (projectname != null && !projectname.trim().isEmpty()) {
            sql.append(" AND projectname LIKE ?");
            params.add("%" + projectname + "%");
        }

        // 状态查询
        if (status != null && !status.trim().isEmpty()) {
            sql.append(" AND status = ?");
            params.add(status);
        }

        // 年份查询
        if (year != null && !year.trim().isEmpty()) {
            sql.append(" AND year LIKE ?");
            params.add("%" + year + "%");
        }

        // 地点模糊查询
        if (location != null && !location.trim().isEmpty()) {
            sql.append(" AND location LIKE ?");
            params.add("%" + location + "%");
        }

        try {
            DataUtil dataUtil = new DataUtil();
            ResultSet rs = dataUtil.select(sql.toString(), params.toArray());
            list = TpTable.tranList(rs);
            dataUtil.close();
        } catch (Exception e) {
            e.printStackTrace();
        }

        return list;
    }



}
