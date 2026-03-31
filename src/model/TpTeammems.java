package model;

import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

public class TpTeammems {
    private int id;
    private int projectid;
    private int teammemberid;
    private String membertype;
    private String creationtime;
    private String projectname; // 添加项目名称字段

    public TpTeammems(int id, int projectid, int teammemberid,
                      String membertype, String creationtime) {
        this.id = id;
        this.projectid = projectid;
        this.teammemberid = teammemberid;
        this.membertype = membertype;
        this.creationtime = creationtime;

    }

    public TpTeammems() {

    }

    public int getId() {
        return id;
    }

    public int getProjectid() {
        return projectid;
    }

    public int getTeammemberid() {
        return teammemberid;
    }

    public String getMembertype() {
        return membertype;
    }

    public String getCreationtime() {
        return creationtime;
    }

    public void setId(int id) {
        this.id = id;
    }

    public void setProjectid(int projectid) {
        this.projectid = projectid;
    }

    public void setTeammemberid(int teammemberid) {
        this.teammemberid = teammemberid;
    }

    public void setMembertype(String membertype) {
        this.membertype = membertype;
    }

    public void setCreationtime(String creationtime) {
        this.creationtime = creationtime;
    }

    @Override
    public String toString() {
        return "TpTeammems{" +
                "id=" + id +
                ", projectid=" + projectid +
                ", teammemberid=" + teammemberid +
                ", membertype='" + membertype + '\'' +
                ", creationtime='" + creationtime + '\'' +
                '}';
    }

    public TpTeammems(ResultSet rs) {
        try {
            if (rs != null && rs.next()) {
                this.setId(rs.getInt("id"));
                this.setProjectid(rs.getInt("projectid"));
                this.setTeammemberid(rs.getInt("teammemberid"));
                this.setMembertype(rs.getString("membertype"));
                this.setCreationtime(rs.getString("creationtime"));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static List<TpTeammems> tranList(ResultSet rs){
        List<TpTeammems> list = new ArrayList<>();
        try {
            while (rs != null && rs.next()) {
                TpTeammems tm = new TpTeammems();
                tm.setId(rs.getInt("id"));
                tm.setProjectid(rs.getInt("projectid"));
                tm.setTeammemberid(rs.getInt("teammemberid"));
                tm.setMembertype(rs.getString("membertype"));
                tm.setCreationtime(rs.getString("creationtime"));
                list.add(tm);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return list;
    }

    // 添加 getter 和 setter
    public String getProjectname() {
        return projectname;
    }

    public void setProjectname(String projectname) {
        this.projectname = projectname;
    }
}

