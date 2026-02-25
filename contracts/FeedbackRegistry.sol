// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract FeedbackRegistry {
    struct FeedbackRecord {
        string dataHash;
        string encryptedUser;
        string encryptedDescription;
        string targetName;
        string category;
        string priority;
        string organizationId;
        // Ratings stored individually (0-5 scale)
        uint8 rating1;
        uint8 rating2;
        uint8 rating3;
        uint8 rating4;
        // Average rating stored as integer * 100 (e.g. 4.25 = 425)
        uint256 averageRating;
        // Reveal status: "sealed" or "revealed"
        string revealStatus;
        uint256 timestamp;
        bool exists;
    }

    struct AuditLog {
        string action;
        string performedBy;
        string reason;
        uint256 timestamp;
    }

    // feedbackId => FeedbackRecord
    mapping(string => FeedbackRecord) private records;
    
    // feedbackId => AuditLog[]
    mapping(string => AuditLog[]) private auditLogs;

    uint256 public totalFeedbackCount;
    string[] private allFeedbackIds;

    event FeedbackRecorded(
        string feedbackId, 
        string dataHash, 
        string encryptedUser, 
        string targetName,
        string category,
        string priority,
        uint256 timestamp
    );
    event IdentityRevealed(string feedbackId, string performedBy, string reason, uint256 timestamp);
    event RevealStatusUpdated(string feedbackId, string newStatus, uint256 timestamp);

    /**
     * @dev Records a complete feedback on-chain — the single source of truth.
     */
    struct FeedbackInput {
        string feedbackId;
        string dataHash;
        string encryptedUser;
        string encryptedDescription;
        string targetName;
        string category;
        string priority;
        string organizationId;
        uint8 rating1;
        uint8 rating2;
        uint8 rating3;
        uint8 rating4;
        uint256 averageRating;
    }

    /**
     * @dev Records a complete feedback on-chain — the single source of truth.
     */
    function recordFeedback(FeedbackInput memory input) public {
        require(!records[input.feedbackId].exists, "Feedback already recorded");
        
        records[input.feedbackId] = FeedbackRecord({
            dataHash: input.dataHash,
            encryptedUser: input.encryptedUser,
            encryptedDescription: input.encryptedDescription,
            targetName: input.targetName,
            category: input.category,
            priority: input.priority,
            organizationId: input.organizationId,
            rating1: input.rating1,
            rating2: input.rating2,
            rating3: input.rating3,
            rating4: input.rating4,
            averageRating: input.averageRating,
            revealStatus: "sealed",
            timestamp: block.timestamp,
            exists: true
        });

        allFeedbackIds.push(input.feedbackId);
        totalFeedbackCount++;
        emit FeedbackRecorded(
            input.feedbackId, 
            input.dataHash, 
            input.encryptedUser, 
            input.targetName, 
            input.category, 
            input.priority, 
            block.timestamp
        );
    }

    /**
     * @dev Updates the reveal status of a feedback (e.g., "sealed" -> "revealed").
     */
    function updateRevealStatus(string memory feedbackId, string memory newStatus) public {
        require(records[feedbackId].exists, "Feedback does not exist");
        records[feedbackId].revealStatus = newStatus;
        emit RevealStatusUpdated(feedbackId, newStatus, block.timestamp);
    }

    /**
     * @dev Logs an identity reveal action on-chain for audit trail.
     */
    function logIdentityReveal(string memory feedbackId, string memory performedBy, string memory reason) public {
        require(records[feedbackId].exists, "Feedback record does not exist");
        
        auditLogs[feedbackId].push(AuditLog({
            action: "IDENTITY_REVEAL",
            performedBy: performedBy,
            reason: reason,
            timestamp: block.timestamp
        }));

        emit IdentityRevealed(feedbackId, performedBy, reason, block.timestamp);
    }

    /**
     * @dev Verifies a feedback hash against the on-chain record.
     */
    function verifyFeedback(string memory feedbackId, string memory dataHash) public view returns (bool) {
        if (!records[feedbackId].exists) return false;
        return (keccak256(abi.encodePacked(records[feedbackId].dataHash)) == keccak256(abi.encodePacked(dataHash)));
    }

    /**
     * @dev Returns core feedback fields (split to avoid stack-too-deep with solc 0.8.0).
     *      Returns: dataHash, encryptedUser, encryptedDescription, targetName, category, priority, organizationId
     */
    function getFeedbackCore(string memory feedbackId) public view returns (
        string memory dataHash,
        string memory encryptedUser,
        string memory encryptedDescription,
        string memory targetName,
        string memory category,
        string memory priority,
        string memory organizationId
    ) {
        FeedbackRecord storage rec = records[feedbackId];
        return (
            rec.dataHash,
            rec.encryptedUser,
            rec.encryptedDescription,
            rec.targetName,
            rec.category,
            rec.priority,
            rec.organizationId
        );
    }

    /**
     * @dev Returns ratings, averageRating, revealStatus, timestamp and exists flag.
     *      Split from getFeedbackCore to avoid stack-too-deep.
     */
    function getFeedbackMeta(string memory feedbackId) public view returns (
        uint8 rating1,
        uint8 rating2,
        uint8 rating3,
        uint8 rating4,
        uint256 averageRating,
        string memory revealStatus,
        uint256 timestamp,
        bool exists
    ) {
        FeedbackRecord storage rec = records[feedbackId];
        return (
            rec.rating1,
            rec.rating2,
            rec.rating3,
            rec.rating4,
            rec.averageRating,
            rec.revealStatus,
            rec.timestamp,
            rec.exists
        );
    }

    /**
     * @dev Retrieves all feedback IDs recorded on-chain.
     */
    function getAllFeedbackIds() public view returns (string[] memory) {
        return allFeedbackIds;
    }

    /**
     * @dev Retrieves audit logs for a specific feedback ID.
     */
    function getAuditLogs(string memory feedbackId) public view returns (AuditLog[] memory) {
        return auditLogs[feedbackId];
    }
}
