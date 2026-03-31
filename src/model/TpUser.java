package model;

import java.sql.ResultSet;
import java.util.ArrayList;
import java.util.List;

public class TpUser {
    private int userid;
    private String pwd;
    private String usertype;
    private String email;
    private String contactnumber;

    public TpUser(){

    }
    public TpUser(int userid,String pwd,String usertype,String email,String contactnumber){
        this.userid = userid;
        this.pwd = pwd;
        this.usertype = usertype;
        this.email = email;
        this.contactnumber = contactnumber;
    }

    public int getUserid() {
        return userid;
    }

    public String getPwd() {
        return pwd;
    }

    public String getUsertype() {
        return usertype;
    }

    public String getEmail() {
        return email;
    }

    public String getContactnumber() {
        return contactnumber;
    }

    public void setUserid(int userid) {
        this.userid = userid;
    }

    public void setPwd(String pwd) {
        this.pwd = pwd;
    }

    public void setUsertype(String usertype) {
        this.usertype = usertype;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public void setContactnumber(String contactnumber) {
        this.contactnumber = contactnumber;
    }

    @Override
    public String toString() {
        return "TpUser{" +
                "userid=" + userid +
                ", pwd='" + pwd + '\'' +
                ", usertype='" + usertype + '\'' +
                ", email='" + email + '\'' +
                ", contactnumber='" + contactnumber + '\'' +
                '}';
    }

    public TpUser(ResultSet rs) {
        try{
            if (rs != null && rs.next()){
                this.setUserid(rs.getInt("userid"));
                this.setPwd(rs.getString("pwd"));
                this.setUsertype(rs.getString("usertype"));
                this.setEmail(rs.getString("email"));
                this.setContactnumber(rs.getString("contactnumber"));
            }
        }catch(Exception e){
            e.printStackTrace();
        }
    }

    public static List<TpUser> tranList(ResultSet rs) {
        List<TpUser> list = new ArrayList<>();
        try {
            while (rs != null && rs.next()) {
                TpUser user = new TpUser();
                user.setUserid(rs.getInt("userid"));
                user.setPwd(rs.getString("pwd"));
                user.setUsertype(rs.getString("usertype"));
                user.setEmail(rs.getString("email"));
                user.setContactnumber(rs.getString("contactnumber"));
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
        return list;
    }
}
