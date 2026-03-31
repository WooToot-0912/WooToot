package model;


import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class TpTable {
    private int projectid;
    private String projectname;
    private String year;
    private String location;
    private String startdate;
    private String enddate;
    private String notes;
    private String status;

    public TpTable(){
    }

    public TpTable(int projectid, String projectname, String year,
                   String location, String startdate, String enddate, String notes, String status){
        this.projectid = projectid;
        this.projectname = projectname;
        this.year = year;
        this.location = location;
        this.startdate = startdate;
        this.enddate = enddate;
        this.notes = notes;
        this.status = status;
    }

    public int getProjectid() {
        return projectid;
    }

    public String getProjectname() {
        return projectname;
    }

    public String getYear() {
        return year;
    }

    public String getLocation() {
        return location;
    }

    public String getStartdate() {
        return startdate;
    }

    public String getEnddate() {
        return enddate;
    }

    public String getNotes() {
        return notes;
    }

    public String getStatus() {
        return status;
    }

    public void setProjectid(int projectid) {
        this.projectid = projectid;
    }

    public void setProjectname(String projectname) {
        this.projectname = projectname;
    }

    public void setYear(String year) {
        this.year = year;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public void setStartdate(String startdate) {
        this.startdate = startdate;
    }

    public void setEnddate(String enddate) {
        this.enddate = enddate;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    @Override
    public String toString() {
        return "TpTable{" +
                "projectid='" + projectid + '\'' +
                ", projectname='" + projectname + '\'' +
                ", year='" + year + '\'' +
                ", location='" + location + '\'' +
                ", startdate='" + startdate + '\'' +
                ", enddate='" + enddate + '\'' +
                ", notes='" + notes + '\'' +
                ", status='" + status + '\'' +
                '}';
    }
/*
    public TpTable(ResultSet rs){
        try{
            if(rs!=null && rs.next()){
                this.setProjectid(rs.getInt("projectid"));
                this.setProjectname(rs.getString("projectname"));
                this.setYear(rs.getString("year"));
                this.setLocation(rs.getString("location"));
                this.setStartdate(rs.getString("startdate"));
                this.setEnddate(rs.getString("enddate"));
                this.setNotes(rs.getString("notes"));
                this.setStatus(rs.getString("status"));
            }
        }catch (Exception e){
            e.printStackTrace();
        }
    }

 */
public TpTable(ResultSet rs) throws SQLException {
    if (rs != null && rs.next()) {
        this.setProjectid(rs.getInt("projectid"));
        this.setProjectname(rs.getString("projectname"));
        this.setYear(rs.getString("year"));
        this.setLocation(rs.getString("location"));
        this.setStartdate(rs.getString("startdate"));
        this.setEnddate(rs.getString("enddate"));
        this.setNotes(rs.getString("notes"));
        this.setStatus(rs.getString("status"));
    }
}

    public static List<TpTable> tranList(ResultSet rs){
        List<TpTable> list = new ArrayList<>();  //创建一个空的集合数组对象
        try {
            while (rs != null && rs.next()) {
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
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return list;
    }


}
