package test.junit;

import dao.UserDAO;
import dao.UserDaoImpl;
import model.TpUser;
import org.junit.Before;
import org.junit.Test;
import utils.UserTypeProperties;

import static org.junit.Assert.*;

public class UserDaoImplTest {
    private UserDAO udao = null;

    @Before
    public  void init(){
        udao = new UserDaoImpl();//创建用户类管理业务类对象
    }

    @Test
    public void registerUser() {
        TpUser user = new TpUser();
        user.setUserid(15);
        user.setPwd("123456");
        user.setUsertype("管理员");
        user.setEmail("13456@qq.com");
        user.setContactnumber("17508840912");
        //user对象中没有设置的成员就是缺省值
        if (udao.registerUser(user)){//调用业务类对象的业务方法实现用户的注册功能
            System.out.println("用户注册成功");
        }else{
            System.out.println("用户注册失败");
        }
    }

    @Test
    public void login() {
        System.out.println(udao.login("5","password5"));
    }

    @Test
    public void modifyUser() {
        TpUser user = new TpUser();
        user.setUserid(25);
        user.setPwd("password123");
        user.setUsertype("1");
        user.setEmail("13456@qq.com");
        user.setContactnumber("1111111111");
        if (udao.modifyUser(user)){
            System.out.println("用户信息修改成功");
        }else{
            System.out.println("用户信息修改失败");
        }
    }

    @Test
    public void removeUser() {
        System.out.println(udao.removeUser(12));
    }

    @Test
    public void isUseridValid() {
        if (udao.isUseridValid("12")) {
            System.out.println("账号可用");
        }else{
            System.out.println("帐号存在，不可用");
        }
    }

    @Test
    public void getTUserByid() {
        System.out.println(udao.getTUserByid("5"));
    }

    @Test
    public void isTableUser() {
        System.out.println("5账号是管理员吗？"+udao.isTableUser(5));
    }
}