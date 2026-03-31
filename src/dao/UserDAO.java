package dao;

import model.*;

import java.util.List;

/**
 * 用户管理模块接口
 * @author zjs
 */
public interface UserDAO {

    /**
     * 注册用户（添加一个新用户）
     * @param user
     * @return boolean  成功返回true, 失败返回false
     */
    public boolean registerUser(TpUser user);

    /**
     * 用户登录操作方法
     * @param userid
     * @param pwd
     * @return  成功则返回VUser，失败返回null
     */
    public TpUser login(String userid, String pwd);

    /**
     * 修改一个用户信息
     * @param user
     * @return boolean  成功返回true,失败返回false
     */
    public boolean modifyUser(TpUser user);

    /**
     * 删除指定的用户信息
     * @param userid
     * @return 成功返回true，失败返回false
     */
    public boolean removeUser(int userid);

    /**
     * 检查某userid是否可用（已经存在就不可用）
     * @param userid
     * @return 可用（数据库中没有）返回true， 否则返回false
     */
    public boolean isUseridValid(String userid);

    /**
     * 根据userid返回一个TpUser类型的用户对象
     * @param userid
     * @return  TUser   失败返回null
     */
    public TpUser getTUserByid(String userid);

    /**
     * 判断该用户是否为管理员类型
     * @param userid
     * @return boolean,是酒店管理员返回true，否则返回false
     */
    public boolean isTableUser(int userid);

    /**
     * 获取所有用户列表
     * @return 用户列表
     */
    List<TpUser> getAllUsers();
}
