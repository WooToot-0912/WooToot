package model;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class TpExpensebill {
    private int billid;
    private int projectid;
    private String expensetype;
    private String price;
    private String description;
    private String expensetime;
    private String involvedpersons;
    private String projectname;

    public TpExpensebill(){

    }
    public TpExpensebill( int projectid, String expensetype, String price,
                         String description, String expensetime, String involvedpersons){
        this.projectid = projectid;
        this.expensetype = expensetype;
        this.price = price;
        this.description = description;
        this.expensetime = expensetime;
        this.involvedpersons = involvedpersons;

    }

    public int getBillid() {
        return billid;
    }

    public int getProjectid() {
        return projectid;
    }

    public String getExpensetype() {
        return expensetype;
    }

    public String getPrice() {
        return price;
    }

    public String getDescription() {
        return description;
    }

    public String getExpensetime() {
        return expensetime;
    }

    public String getInvolvedpersons() {
        return involvedpersons;
    }

    public String getProjectname() {
        return projectname;
    }

    public void setBillid(int billid) {
        this.billid = billid;
    }

    public void setProjectid(int projectid) {
        this.projectid = projectid;
    }

    public void setExpensetype(String expensetype) {
        this.expensetype = expensetype;
    }

    public void setPrice(String price) {
        this.price = price;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public void setExpensetime(String expensetime) {
        this.expensetime = expensetime;
    }

    public void setInvolvedpersons(String involvedpersons) {
        this.involvedpersons = involvedpersons;
    }

    public void setProjectname(String projectname) {
        this.projectname = projectname;
    }

    @Override
    public String toString() {
        return "TpExpensebill{" +
                "billid=" + billid +
                ", projectid=" + projectid +
                ", expensetype='" + expensetype + '\'' +
                ", price='" + price + '\'' +
                ", description='" + description + '\'' +
                ", expensetime='" + expensetime + '\'' +
                ", involvedpersons='" + involvedpersons + '\'' +
                ", projectname='" + projectname + '\'' +
                '}';
    }

    public TpExpensebill(ResultSet rs) {
        try {
            if (rs != null && rs.next()) {
                this.setBillid(rs.getInt("billid"));
                this.setProjectid(rs.getInt("projectid"));
                this.setExpensetype(rs.getString("expensetype"));
                this.setPrice(rs.getString("price"));
                this.setDescription(rs.getString("description"));
                this.setExpensetime(rs.getString("expensetime"));
                this.setInvolvedpersons(rs.getString("involvedpersons"));
                // 尝试获取项目名称，如果不存在则忽略
                try {
                    this.setProjectname(rs.getString("projectname"));
                } catch (SQLException e) {
                    // 忽略这个错误，因为不是所有查询都会包含 projectname
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    public static List<TpExpensebill> tranList(ResultSet rs) {
        List<TpExpensebill> list = new ArrayList<>();
        try {
            while (rs != null && rs.next()) {
                TpExpensebill bill = new TpExpensebill();
                bill.setBillid(rs.getInt("billid"));
                bill.setProjectid(rs.getInt("projectid"));
                bill.setExpensetype(rs.getString("expensetype"));
                bill.setPrice(rs.getString("price"));
                bill.setDescription(rs.getString("description"));
                bill.setExpensetime(rs.getString("expensetime"));
                bill.setInvolvedpersons(rs.getString("involvedpersons"));
                // 尝试获取项目名称，如果不存在则忽略
                try {
                    bill.setProjectname(rs.getString("projectname"));
                } catch (SQLException e) {
                    // 忽略这个错误
                }
                list.add(bill);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return list;
    }
}
