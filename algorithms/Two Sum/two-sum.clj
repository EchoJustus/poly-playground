(defn two-sum [nums target]
  ;; loop 初始化：idx 从 0 开始，lookup 是一个空的 map {}
  (loop [idx 0
         lookup {}]
    (if (< idx (count nums))
      (let [num (nth nums idx)           ;; 获取当前数值
            complement (- target num)]   ;; 计算需要的差值

        ;; 检查差值是否在 lookup map 中
        (if (contains? lookup complement)
          ;; Case 1: 找到了！返回 [之前的索引, 当前索引]
          [(get lookup complement) idx]

          ;; Case 2: 没找到。递归调用 loop，idx + 1，并将当前数值存入 map
          (recur (inc idx) (assoc lookup num idx))))

      ;; 边界情况：虽然题目保证有解，但习惯上处理一下无解情况
      nil)))
