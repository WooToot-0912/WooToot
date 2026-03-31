package dao;

import model.TpUser;
import utils.DataUtil;
import utils.DataUtil1;
import utils.UserTypeProperties;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class UserDaoImpl implements UserDAO{
    private DataUtil1 dataUtil = null;

    public UserDaoImpl() {
        dataUtil = new DataUtil();
    }

    //注册用户
    @Override
    public boolean registerUser(TpUser user) {
        String sql="insert into tp_user (userid,pwd,usertype,email,contactnumber) values(?,?,?,?,?)";
        Object[] para = {user.getUserid(),user.getPwd(),user.getUsertype(),
                user.getEmail(),user.getContactnumber()};
        int rows = dataUtil.insert(sql,para);
        if(rows>0){
            return true;
        }else
            return false;
    }

    //用户登录
    @Override
    public TpUser login(String userid, String pwd) {
        String  sql="select * from tp_user where userid =? and pwd =?";
        Object[] para = {userid, pwd};
        ResultSet rs = dataUtil.select(sql, para);
        TpUser tu = new TpUser(rs);
        dataUtil.close();
        return tu;//返回用户视图实体对象
    }

    //修改用户信息
    @Override
    public boolean modifyUser(TpUser user) {
        String sql = "update tp_user set userid=?,pwd=?,usertype=?,email=?,contactnumber=?" +
                "where userid=?";
        Object[] para = {user.getUserid(),user.getPwd(),user.getUsertype(),
                user.getEmail(),user.getContactnumber()};
        int rows = dataUtil.update(sql, para);
        if(rows>0) {
            return true;
        }else return false;
    }

    //删除指定的用户信息
    @Override
    public boolean removeUser(int userid) {
        String procName = "delete from tp_user where userid=?";
        Object[] para ={userid};
        try{
            int rs = dataUtil.delete(procName,para);
            if(rs>0)return true;
            else return false;
        }catch(Exception e){
            e.printStackTrace();
        }
        return false;
    }

    @Override
    public boolean isUseridValid(String userid) {
        String sql="select * from tp_user where userid =?";
        Object[] para = {userid};
        int count = dataUtil.selectCount(sql, para);
        if(count>0){//有值的时候说明该userid已经存在了，因此不可用，返回false
            return false;
        } else {  //查询不到，代表该账号可用，返回true
            return true;
        }
    }

    @Override
    public TpUser getTUserByid(String userid) {
        String sql="select * from tp_user where userid =?";
        Object[] para = {userid};
        ResultSet rs = dataUtil.select(sql, para);
        TpUser tu = new TpUser(rs);
        dataUtil.close();
        return tu;
    }


    @Override
    public boolean isTableUser(int userid) {
        String sql="select * from tp_user where userid =?";
        Object[] para = {userid};
        ResultSet rs = dataUtil.select(sql, para);
        TpUser user = new TpUser(rs);
        if(user!=null && user.getUserid() == UserTypeProperties.HOTELADMINTYOE){
            return true;
        }else return false;
    }

    @Override
    public List<TpUser> getAllUsers() {
        String sql = "SELECT * FROM tp_user ORDER BY userid";
        ResultSet rs = dataUtil.select(sql, null);
        List<TpUser> users = new ArrayList<>();
        try {
            while (rs != null && rs.next()) {
                TpUser user = new TpUser();
                user.setUserid(Integer.parseInt(rs.getString("userid")));
                user.setPwd(rs.getString("pwd"));
                user.setUsertype(rs.getString("usertype"));
                user.setEmail(rs.getString("email"));
                user.setContactnumber(rs.getString("contactnumber"));
                users.add(user);
            }
        } catch (SQLException e) {
            e.printStackTrace();
        } finally {
            dataUtil.close();
        }
        return users;
    }

}
