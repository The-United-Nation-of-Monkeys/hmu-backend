// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title GrantManager
 * @dev Смарт-контракт для управления грантовыми средствами
 */
contract GrantManager {
    // Структура гранта
    struct Grant {
        uint256 id;
        address recipient;           // Получатель гранта
        uint256 amount;              // Сумма гранта
        uint256 allocatedAmount;     // Выделенная сумма
        uint256 releasedAmount;      // Выпущенная сумма
        string description;          // Описание гранта
        GrantStatus status;          // Статус гранта
        uint256 createdAt;           // Дата создания
        uint256 deadline;            // Срок выполнения
        bool requiresApproval;       // Требуется ли одобрение
        uint256 approvalCount;       // Количество одобрений
        mapping(address => bool) approvals; // Кто одобрил
    }

    enum GrantStatus {
        Pending,      // Ожидает одобрения
        Approved,     // Одобрен
        Active,       // Активен
        Completed,    // Завершен
        Cancelled     // Отменен
    }

    // Владелец контракта (администратор)
    address public owner;
    
    // Минимальное количество одобрений для мультиподписи
    uint256 public minApprovals;
    
    // Адреса, имеющие право одобрять гранты
    mapping(address => bool) public approvers;
    
    // Маппинг грантов
    mapping(uint256 => Grant) public grants;
    
    // Счетчик грантов
    uint256 public grantCount;
    
    // События
    event GrantCreated(
        uint256 indexed grantId,
        address indexed recipient,
        uint256 amount,
        string description
    );
    
    event GrantApproved(
        uint256 indexed grantId,
        address indexed approver
    );
    
    event FundsAllocated(
        uint256 indexed grantId,
        uint256 amount
    );
    
    event FundsReleased(
        uint256 indexed grantId,
        address indexed recipient,
        uint256 amount
    );
    
    event GrantStatusChanged(
        uint256 indexed grantId,
        GrantStatus oldStatus,
        GrantStatus newStatus
    );
    
    event ApproverAdded(address indexed approver);
    event ApproverRemoved(address indexed approver);

    // Модификаторы
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    modifier onlyApprover() {
        require(approvers[msg.sender], "Only approver can call this function");
        _;
    }
    
    modifier validGrant(uint256 _grantId) {
        require(_grantId > 0 && _grantId <= grantCount, "Invalid grant ID");
        _;
    }

    /**
     * @dev Конструктор контракта
     * @param _minApprovals Минимальное количество одобрений
     */
    constructor(uint256 _minApprovals) {
        owner = msg.sender;
        minApprovals = _minApprovals;
        approvers[msg.sender] = true;
    }

    /**
     * @dev Создание нового гранта
     * @param _recipient Адрес получателя
     * @param _amount Сумма гранта
     * @param _description Описание гранта
     * @param _deadline Срок выполнения (timestamp)
     * @param _requiresApproval Требуется ли одобрение
     */
    function createGrant(
        address _recipient,
        uint256 _amount,
        string memory _description,
        uint256 _deadline,
        bool _requiresApproval
    ) external onlyOwner returns (uint256) {
        require(_recipient != address(0), "Invalid recipient address");
        require(_amount > 0, "Amount must be greater than 0");
        require(_deadline > block.timestamp, "Deadline must be in the future");

        grantCount++;
        Grant storage grant = grants[grantCount];
        
        grant.id = grantCount;
        grant.recipient = _recipient;
        grant.amount = _amount;
        grant.description = _description;
        grant.deadline = _deadline;
        grant.requiresApproval = _requiresApproval;
        grant.createdAt = block.timestamp;
        
        if (_requiresApproval) {
            grant.status = GrantStatus.Pending;
        } else {
            grant.status = GrantStatus.Approved;
        }

        emit GrantCreated(grantCount, _recipient, _amount, _description);
        return grantCount;
    }

    /**
     * @dev Одобрение гранта
     * @param _grantId ID гранта
     */
    function approveGrant(uint256 _grantId) external onlyApprover validGrant(_grantId) {
        Grant storage grant = grants[_grantId];
        require(grant.requiresApproval, "Grant does not require approval");
        require(grant.status == GrantStatus.Pending, "Grant is not pending");
        require(!grant.approvals[msg.sender], "Already approved");

        grant.approvals[msg.sender] = true;
        grant.approvalCount++;

        emit GrantApproved(_grantId, msg.sender);

        if (grant.approvalCount >= minApprovals) {
            grant.status = GrantStatus.Approved;
            emit GrantStatusChanged(_grantId, GrantStatus.Pending, GrantStatus.Approved);
        }
    }

    /**
     * @dev Выделение средств для гранта
     * @param _grantId ID гранта
     * @param _amount Сумма для выделения
     */
    function allocateFunds(uint256 _grantId, uint256 _amount) 
        external 
        onlyOwner 
        validGrant(_grantId) 
    {
        Grant storage grant = grants[_grantId];
        require(grant.status == GrantStatus.Approved || !grant.requiresApproval, 
                "Grant must be approved");
        require(_amount > 0, "Amount must be greater than 0");
        require(
            grant.allocatedAmount + _amount <= grant.amount,
            "Cannot allocate more than grant amount"
        );

        grant.allocatedAmount += _amount;
        
        if (grant.status == GrantStatus.Approved) {
            grant.status = GrantStatus.Active;
            emit GrantStatusChanged(_grantId, GrantStatus.Approved, GrantStatus.Active);
        }

        emit FundsAllocated(_grantId, _amount);
    }

    /**
     * @dev Выпуск средств получателю
     * @param _grantId ID гранта
     * @param _amount Сумма для выпуска
     */
    function releaseFunds(uint256 _grantId, uint256 _amount) 
        external 
        onlyOwner 
        validGrant(_grantId) 
    {
        Grant storage grant = grants[_grantId];
        require(grant.status == GrantStatus.Active, "Grant must be active");
        require(_amount > 0, "Amount must be greater than 0");
        require(
            grant.releasedAmount + _amount <= grant.allocatedAmount,
            "Cannot release more than allocated"
        );
        require(
            address(this).balance >= _amount,
            "Insufficient contract balance"
        );

        grant.releasedAmount += _amount;
        
        if (grant.releasedAmount == grant.amount) {
            grant.status = GrantStatus.Completed;
            emit GrantStatusChanged(_grantId, GrantStatus.Active, GrantStatus.Completed);
        }

        (bool success, ) = grant.recipient.call{value: _amount}("");
        require(success, "Transfer failed");

        emit FundsReleased(_grantId, grant.recipient, _amount);
    }

    /**
     * @dev Отмена гранта
     * @param _grantId ID гранта
     */
    function cancelGrant(uint256 _grantId) external onlyOwner validGrant(_grantId) {
        Grant storage grant = grants[_grantId];
        require(
            grant.status == GrantStatus.Pending || grant.status == GrantStatus.Approved,
            "Cannot cancel grant in current status"
        );

        GrantStatus oldStatus = grant.status;
        grant.status = GrantStatus.Cancelled;
        emit GrantStatusChanged(_grantId, oldStatus, GrantStatus.Cancelled);
    }

    /**
     * @dev Добавление одобряющего
     * @param _approver Адрес одобряющего
     */
    function addApprover(address _approver) external onlyOwner {
        require(_approver != address(0), "Invalid approver address");
        require(!approvers[_approver], "Already an approver");
        
        approvers[_approver] = true;
        emit ApproverAdded(_approver);
    }

    /**
     * @dev Удаление одобряющего
     * @param _approver Адрес одобряющего
     */
    function removeApprover(address _approver) external onlyOwner {
        require(approvers[_approver], "Not an approver");
        
        approvers[_approver] = false;
        emit ApproverRemoved(_approver);
    }

    /**
     * @dev Изменение минимального количества одобрений
     * @param _minApprovals Новое минимальное количество
     */
    function setMinApprovals(uint256 _minApprovals) external onlyOwner {
        require(_minApprovals > 0, "Min approvals must be greater than 0");
        minApprovals = _minApprovals;
    }

    /**
     * @dev Получение информации о гранте
     * @param _grantId ID гранта
     */
    function getGrant(uint256 _grantId) 
        external 
        view 
        validGrant(_grantId) 
        returns (
            uint256 id,
            address recipient,
            uint256 amount,
            uint256 allocatedAmount,
            uint256 releasedAmount,
            string memory description,
            GrantStatus status,
            uint256 createdAt,
            uint256 deadline,
            bool requiresApproval,
            uint256 approvalCount
        ) 
    {
        Grant storage grant = grants[_grantId];
        return (
            grant.id,
            grant.recipient,
            grant.amount,
            grant.allocatedAmount,
            grant.releasedAmount,
            grant.description,
            grant.status,
            grant.createdAt,
            grant.deadline,
            grant.requiresApproval,
            grant.approvalCount
        );
    }

    /**
     * @dev Проверка, одобрил ли адрес грант
     * @param _grantId ID гранта
     * @param _approver Адрес одобряющего
     */
    function hasApproved(uint256 _grantId, address _approver) 
        external 
        view 
        validGrant(_grantId) 
        returns (bool) 
    {
        return grants[_grantId].approvals[_approver];
    }

    /**
     * @dev Получение баланса контракта
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }

    /**
     * @dev Пополнение контракта средствами
     */
    function deposit() external payable {
        require(msg.value > 0, "Must send some ether");
    }

    /**
     * @dev Вывод средств владельцем (только нераспределенные средства)
     */
    function withdraw(uint256 _amount) external onlyOwner {
        require(_amount > 0, "Amount must be greater than 0");
        require(address(this).balance >= _amount, "Insufficient balance");
        
        (bool success, ) = owner.call{value: _amount}("");
        require(success, "Transfer failed");
    }
}

