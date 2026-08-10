<?php
/**
 * Created by PhpStorm.
 * User: wangyu
 * Date: 2018/9/4
 * Time: 0:03
 */

namespace App\Models;

use Core\Model;
use PDO;

class Post extends Model
{
    protected $title;
    protected $content;
    protected $imgUrl;
    /**
     * @return array
     */
    public static function getTop10()
    {
        $sql = "select post.*,count(comment.id) as commentCount from post left join comment on post.id
        = comment.postId group by post.id order by createdAt desc limit 10";
        $db = static::getDB();
        $stmt = $db->query($sql);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    public static function getById(int $id)
    {
        $sql = "select * from post where `id` = {$id}";
        $db = static::getDB();
        $stmt = $db->query($sql);
        return $stmt->fetch(PDO::FETCH_ASSOC);
    }

    /**
     * @return mixed
     */
    public function getTitle()
    {
        return $this->title;
    }

    /**
     * @param mixed $title
     */
    public function setTitle($title)
    {
        $this->title = $title;
    }

    /**
     * @return mixed
     */
    public function getContent()
    {
        return $this->content;
    }

    /**
     * @param mixed $content
     */
    public function setContent($content)
    {
        $this->content = $content;
    }

    /**
     * @return mixed
     */
    public function getImgUrl()
    {
        return $this->imgUrl;
    }

    /**
     * @param mixed $imgUrl
     */
    public function setImgUrl($imgUrl)
    {
        $this->imgUrl = $imgUrl;
    }

    /**
     * 创建文章
     * @return bool
     */
    public function create()
    {
        $sql = "insert into `post` (title, imgUrl, content, createdAt, updatedAt) 
            VALUES(:title, :imgUrl, :content, :createdAt, :updatedAt)";
        $db = static::getDB();
        $stmt = $db->prepare($sql);
        $stmt->bindParam(':title', $this->title);
        $stmt->bindParam(':imgUrl', $this->imgUrl);
        $stmt->bindParam(':content', $this->content);
        $stmt->bindValue(':createdAt', date("Y-m-d H:i:s"));
        $stmt->bindValue(':updatedAt', date("Y-m-d H:i:s"));
        return $stmt->execute();
    }

}